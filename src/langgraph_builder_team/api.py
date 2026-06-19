from __future__ import annotations

from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse

from .auth import clear_auth_cookie, require_auth, set_auth_cookie, verify_session
from .deep_agents_adapter import deep_agents_code, deep_agents_js_code, open_swe_task_payload
from .graph import run_build
from .integrations import integration_matrix
from .langconnect_adapter import LangConnectUnavailable, query_langconnect
from .llm import LLMUnavailable, OpenAICompatibleLLM
from .mcp_adapters import list_mcp_tools
from .models import (
    AgentProtocolRunCreate,
    AgentProtocolThreadCreate,
    BuildRequest,
    BuildResponse,
    ChatMessageRequest,
    LangConnectQueryRequest,
    LLMCompletionRequest,
    LoginRequest,
    MemorySearchRequest,
    MemoryUpsertRequest,
    OpenSWETaskRequest,
)
from .settings import get_settings
from .storage import HybridBuildArchive
from .vector_memory import HybridMemory

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _project_path(name: str) -> Path:
    for base in (Path.cwd(), PACKAGE_ROOT):
        candidate = base / name
        if candidate.exists():
            return candidate
    return Path.cwd() / name


AGENTS_DIR = _project_path("agents")
TEMPLATES_DIR = _project_path("templates")
PROMPTS_DIR = _project_path("prompts")

BUILD_HISTORY_LOCK = Lock()
MAX_HISTORY_ITEMS = 25
ARCHIVE = HybridBuildArchive(max_items=MAX_HISTORY_ITEMS)
MEMORY = HybridMemory()
LLM = OpenAICompatibleLLM()


def _build_response(request: BuildRequest) -> BuildResponse:
    state = run_build(request.user_request, request.project_id)
    return BuildResponse(
        project_id=state.project_id,
        status=state.status,
        quality_score=state.quality_score,
        plan=state.plan,
        artifacts=state.generated_artifacts,
        review_feedback=state.review_feedback,
        verification_result=state.verification_result,
        deployment_instructions=state.deployment_instructions,
    )


def _remember_build(response: BuildResponse) -> None:
    with BUILD_HISTORY_LOCK:
        ARCHIVE.save_build(response)
        MEMORY.upsert(
            response.project_id,
            f"Build {response.project_id}: status={response.status} score={response.quality_score}",
            {"kind": "build_summary", "quality_score": response.quality_score},
        )


def _list_markdown(directory: Path) -> list[dict[str, str]]:
    if not directory.exists():
        return []
    items = []
    for path in sorted(directory.glob("*.md")):
        items.append({"name": path.stem, "filename": path.name, "content": path.read_text()})
    return items


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/metadata")
def metadata(request: Request) -> dict[str, object]:
    require_auth(request)
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "quality_threshold": settings.quality_threshold,
        "auth": {
            "enabled": settings.auth_enabled,
            "authenticated": True,
            "username": settings.auth_username if settings.auth_enabled else None,
        },
        "memory": {
            "postgres_dsn_configured": bool(settings.postgres_dsn),
            "postgres_checkpointer_enabled": settings.postgres_checkpointer_enabled,
            "postgres_archive_available": ARCHIVE.last_error is None,
            "qdrant_url": settings.qdrant_url,
            "project_memory_collection": settings.project_memory_collection,
            "global_memory_collection": settings.global_memory_collection,
            "qdrant_available": MEMORY.last_error is None,
        },
        "llm": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "base_url": settings.llm_base_url or "OpenAI default",
            "configured": LLM.configured,
        },
        "integrations": integration_matrix(),
        "secrets": {
            "openai_api_key_set": bool(settings.openai_api_key),
            "anthropic_api_key_set": bool(settings.anthropic_api_key),
            "langsmith_api_key_set": bool(settings.langsmith_api_key),
            "where_to_set": ".env locally, VPS environment variables, or your secret manager",
        },
        "paths": {
            "agent_specs": "agents/",
            "system_prompts": "prompts/",
            "skills": "skills/",
            "templates": "templates/",
            "reports": "docs/reports/",
            "archive_recommendation": "Use a persistent DB/object storage for generated artifacts",
        },
    }


@app.get("/agents")
def agents(request: Request) -> dict[str, list[dict[str, str]]]:
    require_auth(request)
    return {"agents": _list_markdown(AGENTS_DIR)}


@app.get("/templates")
def templates(request: Request) -> dict[str, list[dict[str, str]]]:
    require_auth(request)
    return {"templates": _list_markdown(TEMPLATES_DIR)}


@app.get("/prompts")
def prompts(request: Request) -> dict[str, list[dict[str, str]]]:
    require_auth(request)
    return {"prompts": _list_markdown(PROMPTS_DIR)}


@app.get("/builds", response_model=list[BuildResponse])
def builds(request: Request) -> list[BuildResponse]:
    require_auth(request)
    with BUILD_HISTORY_LOCK:
        return ARCHIVE.list_builds()


@app.get("/builds/{project_id}", response_model=BuildResponse)
def build_detail(project_id: str, request: Request) -> BuildResponse:
    require_auth(request)
    with BUILD_HISTORY_LOCK:
        item = ARCHIVE.get_build(project_id)
        if item:
            return item
    raise HTTPException(status_code=404, detail="Build not found")


@app.post("/auth/login")
def login(payload: LoginRequest) -> JSONResponse:
    if not settings.auth_enabled:
        return JSONResponse({"authenticated": True, "auth_enabled": False})
    if not settings.auth_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_PASSWORD is not configured",
        )
    if payload.username != settings.auth_username or payload.password != settings.auth_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    response = JSONResponse({"authenticated": True, "auth_enabled": True})
    set_auth_cookie(response, payload.username)
    return response


@app.get("/auth/status")
def auth_status(request: Request) -> dict[str, object]:
    return {
        "auth_enabled": settings.auth_enabled,
        "authenticated": verify_session(request.cookies.get(settings.auth_cookie_name)),
    }


@app.post("/auth/logout")
def logout() -> JSONResponse:
    response = JSONResponse({"authenticated": False})
    clear_auth_cookie(response)
    return response


@app.get("/chat/{project_id}")
def chat_history(project_id: str, request: Request) -> dict[str, object]:
    require_auth(request)
    return {"messages": ARCHIVE.list_chat_messages(project_id), "storage_error": ARCHIVE.last_error}


@app.post("/chat")
def add_chat_message(payload: ChatMessageRequest, request: Request) -> dict[str, object]:
    require_auth(request)
    message = ARCHIVE.add_chat_message(payload.project_id, payload.role, payload.content)
    MEMORY.upsert(
        payload.project_id,
        payload.content,
        {"kind": "chat", "role": payload.role},
    )
    return {"message": message, "storage_error": ARCHIVE.last_error}


@app.post("/memory/upsert")
def memory_upsert(payload: MemoryUpsertRequest, request: Request) -> dict[str, object]:
    require_auth(request)
    point_id = MEMORY.upsert(payload.project_id, payload.text, payload.metadata)
    return {"id": point_id, "qdrant_error": MEMORY.last_error}


@app.post("/memory/search")
def memory_search(payload: MemorySearchRequest, request: Request) -> dict[str, object]:
    require_auth(request)
    return {
        "results": MEMORY.search(payload.query, payload.project_id, payload.limit),
        "qdrant_error": MEMORY.last_error,
    }


@app.post("/llm/complete")
def llm_complete(payload: LLMCompletionRequest, request: Request) -> dict[str, object]:
    require_auth(request)
    try:
        return {"content": LLM.complete(payload.prompt, payload.system), "configured": True}
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/integrations")
def integrations(request: Request) -> dict[str, object]:
    require_auth(request)
    return {"integrations": integration_matrix()}


@app.get("/integrations/deep-agents/code")
def deep_agents_python_code(request: Request) -> dict[str, str]:
    require_auth(request)
    return {"language": "python", "content": deep_agents_code()}


@app.get("/integrations/deep-agents/js-code")
def deep_agents_javascript_code(request: Request) -> dict[str, str]:
    require_auth(request)
    return {"language": "typescript", "content": deep_agents_js_code()}


@app.post("/integrations/open-swe/task")
def open_swe_task(payload: OpenSWETaskRequest, request: Request) -> dict[str, object]:
    require_auth(request)
    return open_swe_task_payload(payload)


@app.post("/integrations/langconnect/query")
def langconnect_query(payload: LangConnectQueryRequest, request: Request) -> dict[str, object]:
    require_auth(request)
    try:
        return query_langconnect(payload)
    except LangConnectUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/mcp/tools")
async def mcp_tools(request: Request) -> dict[str, object]:
    require_auth(request)
    try:
        return {"tools": await list_mcp_tools(), "configured": bool(settings.mcp_servers_json)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/agent-protocol/info")
def agent_protocol_info(request: Request) -> dict[str, object]:
    require_auth(request)
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "enabled": settings.agent_protocol_enabled,
        "capabilities": ["threads", "runs", "stateful-builds", "chat-history"],
    }


@app.post("/agent-protocol/threads")
def agent_protocol_create_thread(
    payload: AgentProtocolThreadCreate,
    request: Request,
) -> dict[str, object]:
    require_auth(request)
    thread_id = payload.thread_id or payload.project_id or f"thread-{uuid4().hex[:12]}"
    for message in payload.messages:
        ARCHIVE.add_chat_message(thread_id, message.role, message.content)
        MEMORY.upsert(thread_id, message.content, {"kind": "agent_protocol_message", "role": message.role})
    return {
        "thread_id": thread_id,
        "project_id": payload.project_id or thread_id,
        "metadata": payload.metadata,
        "messages": ARCHIVE.list_chat_messages(thread_id),
    }


@app.get("/agent-protocol/threads/{thread_id}")
def agent_protocol_get_thread(thread_id: str, request: Request) -> dict[str, object]:
    require_auth(request)
    return {"thread_id": thread_id, "messages": ARCHIVE.list_chat_messages(thread_id)}


@app.post("/agent-protocol/runs")
def agent_protocol_create_run(
    payload: AgentProtocolRunCreate,
    request: Request,
) -> dict[str, object]:
    require_auth(request)
    project_id = payload.project_id or payload.thread_id
    ARCHIVE.add_chat_message(payload.thread_id, "user", payload.input)
    response = _build_response(BuildRequest(user_request=payload.input, project_id=project_id))
    _remember_build(response)
    ARCHIVE.add_chat_message(
        payload.thread_id,
        "assistant",
        f"Build {response.project_id} completed with score {response.quality_score}.",
    )
    return {
        "run_id": f"run-{uuid4().hex[:12]}",
        "thread_id": payload.thread_id,
        "project_id": response.project_id,
        "status": response.status,
        "output": response.model_dump(mode="json"),
        "metadata": payload.metadata,
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="de">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>LangGraph Builder Team</title>
        <style>
          :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --panel: #ffffff;
            --panel-2: #eef3f8;
            --text: #17202a;
            --muted: #667085;
            --line: #d8dee8;
            --accent: #1f7a6d;
            --accent-2: #265caa;
            --danger: #b42318;
            --ok: #067647;
            --warn: #b54708;
            --shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            color: var(--text);
          }
          button, input, textarea, select { font: inherit; }
          .shell { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
          aside {
            background: #111827;
            color: #f8fafc;
            padding: 24px 18px;
            position: sticky;
            top: 0;
            height: 100vh;
          }
          .brand { font-size: 20px; font-weight: 750; margin-bottom: 6px; }
          .sub { color: #bac4d4; font-size: 13px; line-height: 1.5; margin-bottom: 22px; }
          .nav { display: grid; gap: 8px; }
          .nav button {
            border: 0;
            border-radius: 8px;
            padding: 11px 12px;
            text-align: left;
            color: #dbe4ef;
            background: transparent;
            cursor: pointer;
          }
          .nav button.active, .nav button:hover { background: #243044; color: #fff; }
          main { padding: 26px; }
          .topbar {
            display: flex;
            gap: 14px;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 22px;
          }
          h1 { font-size: 28px; margin: 0; letter-spacing: 0; }
          h2 { font-size: 18px; margin: 0 0 14px; }
          h3 { font-size: 15px; margin: 0 0 10px; }
          .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: #fff;
            padding: 8px 12px;
            color: var(--muted);
            font-size: 13px;
          }
          .dot { width: 8px; height: 8px; border-radius: 999px; background: var(--warn); }
          .dot.ok { background: var(--ok); }
          .grid { display: grid; gap: 18px; }
          .cols { grid-template-columns: minmax(0, 1.25fr) minmax(320px, .75fr); }
          .cards { grid-template-columns: repeat(4, minmax(150px, 1fr)); }
          .panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: var(--shadow);
            padding: 18px;
          }
          .metric { min-height: 94px; }
          .metric .label { color: var(--muted); font-size: 12px; }
          .metric .value { font-size: 26px; font-weight: 750; margin-top: 10px; }
          .field { display: grid; gap: 7px; margin-bottom: 14px; }
          label { color: #344054; font-size: 13px; font-weight: 650; }
          textarea, input, select {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #fff;
            color: var(--text);
            padding: 11px 12px;
            outline: none;
          }
          textarea { min-height: 220px; resize: vertical; line-height: 1.45; }
          textarea:focus, input:focus, select:focus { border-color: var(--accent-2); box-shadow: 0 0 0 3px rgba(38, 92, 170, .12); }
          .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
          .actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
          .btn {
            border: 0;
            border-radius: 8px;
            background: var(--accent);
            color: #fff;
            padding: 11px 14px;
            font-weight: 700;
            cursor: pointer;
          }
          .btn.secondary { background: #344054; }
          .btn.ghost { background: #fff; color: var(--text); border: 1px solid var(--line); }
          .btn:disabled { opacity: .55; cursor: not-allowed; }
          .help { color: var(--muted); font-size: 13px; line-height: 1.5; }
          pre {
            white-space: pre-wrap;
            word-break: break-word;
            margin: 0;
            background: #111827;
            color: #d7e2ef;
            border-radius: 8px;
            padding: 14px;
            max-height: 420px;
            overflow: auto;
            font-size: 12px;
          }
          .list { display: grid; gap: 10px; }
          .item {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 12px;
            background: #fff;
          }
          .item strong { display: block; margin-bottom: 4px; }
          .pill {
            display: inline-flex;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 12px;
            background: var(--panel-2);
            color: #344054;
            margin: 2px 4px 2px 0;
          }
          .screen { display: none; }
          .screen.active { display: grid; gap: 18px; }
          .artifact { cursor: pointer; }
          .artifact:hover { border-color: var(--accent-2); }
          .settings-table { width: 100%; border-collapse: collapse; }
          .settings-table th, .settings-table td {
            border-bottom: 1px solid var(--line);
            text-align: left;
            padding: 10px 8px;
            vertical-align: top;
            font-size: 13px;
          }
          .settings-table th { color: var(--muted); font-weight: 700; }
          .hidden { display: none; }
          @media (max-width: 980px) {
            .shell { grid-template-columns: 1fr; }
            aside { position: static; height: auto; }
            .cols, .cards, .row { grid-template-columns: 1fr; }
            main { padding: 18px; }
            .topbar { align-items: flex-start; flex-direction: column; }
          }
        </style>
      </head>
      <body>
        <div class="shell">
          <aside>
            <div class="brand">LangGraph Builder Team</div>
            <div class="sub">Planen, bauen, testen, reviewen und deployen von Agent-Projekten.</div>
            <div class="nav">
              <button class="active" data-tab="builder">Build Studio</button>
              <button data-tab="agents">Agenten</button>
              <button data-tab="memory">Memory & Archiv</button>
              <button data-tab="integrations">Integrationen</button>
              <button data-tab="settings">Settings</button>
              <button data-tab="deployment">Deployment</button>
              <button data-tab="history">History</button>
            </div>
          </aside>

          <main>
            <div class="topbar">
              <div>
                <h1>Build Studio</h1>
                <div class="help">Arbeitsoberflaeche fuer Builder-Requests, Optionen, Artefakte und Review-Ergebnisse.</div>
              </div>
              <div class="status"><span id="health-dot" class="dot"></span><span id="health-text">checking</span></div>
            </div>

            <section id="builder" class="screen active">
              <div class="grid cards">
                <div class="panel metric"><div class="label">Quality Gate</div><div id="metric-score" class="value">-</div></div>
                <div class="panel metric"><div class="label">Status</div><div id="metric-status" class="value">-</div></div>
                <div class="panel metric"><div class="label">Artefakte</div><div id="metric-artifacts" class="value">0</div></div>
                <div class="panel metric"><div class="label">Builds</div><div id="metric-builds" class="value">0</div></div>
              </div>

              <div class="grid cols">
                <div class="panel">
                  <h2>Request planen</h2>
                  <div class="field">
                    <label for="project-id">Project ID</label>
                    <input id="project-id" placeholder="optional, z.B. customer-support-agent" />
                  </div>
                  <div class="row">
                    <div class="field">
                      <label for="target">Deployment Ziel</label>
                      <select id="target">
                        <option>docker-compose</option>
                        <option>vps</option>
                        <option>k3s</option>
                        <option>local-only</option>
                      </select>
                    </div>
                    <div class="field">
                      <label for="quality">Quality Threshold</label>
                      <input id="quality" type="number" min="0" max="100" value="75" />
                    </div>
                  </div>
                  <div class="field">
                    <label for="request">Builder Request</label>
                    <textarea id="request">Baue einen production-ready LangGraph Agent Workflow mit Planning, Agent Builder, Sandbox Tests, Review, Verification, Memory, Archiv, Settings und VPS Deployment.</textarea>
                  </div>
                  <div class="actions">
                    <button id="run-build" class="btn">Build starten</button>
                    <button id="load-example" class="btn ghost">Beispiel laden</button>
                    <button id="clear-output" class="btn ghost">Output leeren</button>
                  </div>
                </div>

                <div class="panel">
                  <h2>Build Ergebnis</h2>
                  <div id="summary" class="help">Noch kein Build ausgefuehrt.</div>
                  <div style="height: 12px"></div>
                  <pre id="output">Bereit.</pre>
                </div>
              </div>

              <div class="grid cols">
                <div class="panel">
                  <h2>Plan</h2>
                  <pre id="plan-output">Kein Plan vorhanden.</pre>
                </div>
                <div class="panel">
                  <h2>Artefakte</h2>
                  <div id="artifacts" class="list"></div>
                </div>
              </div>
            </section>

            <section id="agents" class="screen">
              <div class="panel">
                <h2>Agenten bauen und pflegen</h2>
                <div class="help">Agent Specs liegen in <code>agents/</code>, System Prompts in <code>prompts/</code>. Neue Agenten sollten zuerst als Spec geplant, dann als Node implementiert und danach getestet werden.</div>
              </div>
              <div id="agent-list" class="grid cols"></div>
            </section>

            <section id="memory" class="screen">
              <div class="grid cols">
                <div class="panel">
                  <h2>Memory & Chat History</h2>
                  <p class="help">Kurzfristiger Runtime-State lebt im `BuilderState`. Production-Checkpoints sollen in Postgres liegen. Projekt- und globale Wissenssuche sind fuer Qdrant vorbereitet.</p>
                  <div id="memory-info" class="list"></div>
                  <div style="height: 14px"></div>
                  <div class="field">
                    <label for="chat-project">Chat Project ID</label>
                    <input id="chat-project" placeholder="z.B. langgraph-builder-production" />
                  </div>
                  <div class="field">
                    <label for="chat-content">Chat / Plan Notiz</label>
                    <textarea id="chat-content" style="min-height: 110px" placeholder="Notiz oder Chat-Nachricht speichern"></textarea>
                  </div>
                  <div class="actions">
                    <button id="save-chat" class="btn">Chat speichern</button>
                    <button id="load-chat" class="btn ghost">History laden</button>
                  </div>
                  <div style="height: 12px"></div>
                  <div id="chat-list" class="list"></div>
                </div>
                <div class="panel">
                  <h2>Qdrant Memory Search</h2>
                  <p class="help">Builds und Chat-Nachrichten werden in Qdrant indexiert, wenn Qdrant erreichbar ist. Ohne Qdrant nutzt die App einen lokalen Fallback fuer Tests.</p>
                  <div class="field">
                    <label for="memory-query">Suchanfrage</label>
                    <input id="memory-query" placeholder="z.B. sandbox tester deployment" />
                  </div>
                  <div class="actions">
                    <button id="search-memory" class="btn">Memory suchen</button>
                  </div>
                  <div style="height: 12px"></div>
                  <div id="memory-results" class="list"></div>
                  <div style="height: 16px"></div>
                  <h2>Archiv</h2>
                  <p class="help">Builds und Chat-History werden in Postgres persistiert, wenn die DB erreichbar ist. Artefakte bleiben zusaetzlich im Build-Payload versioniert.</p>
                  <div class="pill">docs/reports/</div>
                  <div class="pill">generated_artifacts</div>
                  <div class="pill">project_id namespace</div>
                </div>
              </div>
            </section>

            <section id="integrations" class="screen">
              <div class="panel">
                <h2>Frameworks & Adapter</h2>
                <p class="help">Status fuer LangChain, LangGraph, Deep Agents, MCP, Agent Protocol, Open SWE, LangSmith und JS-Starter. Werte kommen aus Backend-Konfiguration und vorhandenen Adapter-Dateien.</p>
                <div id="integration-list" class="grid cols"></div>
              </div>
              <div class="grid cols">
                <div class="panel">
                  <h2>Agent Protocol</h2>
                  <pre>POST /agent-protocol/threads
POST /agent-protocol/runs
GET /agent-protocol/threads/{thread_id}</pre>
                </div>
                <div class="panel">
                  <h2>MCP & Open SWE</h2>
                  <pre>GET /mcp/tools
POST /integrations/open-swe/task
GET /integrations/deep-agents/code</pre>
                </div>
              </div>
            </section>

            <section id="settings" class="screen">
              <div class="panel">
                <h2>Settings & API Keys</h2>
                <p class="help">API Keys werden nicht im UI gesetzt oder angezeigt. Lokal kommen sie in `.env`, auf dem VPS in Environment Variables oder einen Secret Manager. Der Server zeigt hier nur, ob ein Key gesetzt ist.</p>
                <table class="settings-table" id="settings-table"></table>
              </div>
              <div class="panel">
                <h2>Templates</h2>
                <div id="template-list" class="list"></div>
              </div>
              <div class="panel">
                <h2>LLM Adapter Test</h2>
                <p class="help">OpenAI-kompatibler Adapter. Setze `OPENAI_API_KEY`, optional `LLM_BASE_URL` und `LLM_MODEL` in `.env` oder auf dem VPS.</p>
                <div class="field">
                  <label for="llm-prompt">Prompt</label>
                  <textarea id="llm-prompt" style="min-height: 120px">Antworte mit einem kurzen Systemstatus.</textarea>
                </div>
                <div class="actions">
                  <button id="run-llm" class="btn secondary">LLM testen</button>
                </div>
                <div style="height: 12px"></div>
                <pre id="llm-output">Kein LLM-Test ausgefuehrt.</pre>
              </div>
            </section>

            <section id="deployment" class="screen">
              <div class="grid cols">
                <div class="panel">
                  <h2>VPS Ready-to-Start</h2>
                  <pre>cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health</pre>
                  <div style="height: 12px"></div>
                  <p class="help">Remote-Deployment ist mit `scripts/deploy_vps.sh` vorbereitet. Benoetigt werden `VPS_HOST`, `VPS_USER` und optional `VPS_PATH`.</p>
                </div>
                <div class="panel">
                  <h2>Production Checkliste</h2>
                  <div class="list">
                    <div class="item">Starke `POSTGRES_PASSWORD` und passende `POSTGRES_DSN` setzen.</div>
                    <div class="item">API/UI vor oeffentlichem Betrieb mit Auth schuetzen.</div>
                    <div class="item">Reverse Proxy mit TLS konfigurieren.</div>
                    <div class="item">Backups fuer Postgres und Qdrant einrichten.</div>
                    <div class="item">LangSmith/Logging/Metrics aktivieren, sobald Live-LLM-Nodes laufen.</div>
                  </div>
                </div>
              </div>
            </section>

            <section id="history" class="screen">
              <div class="panel">
                <h2>Build History</h2>
                <div class="help">Prozesslokale History der letzten Builds. Fuer dauerhaftes Archiv: Postgres/Object Storage anbinden.</div>
              </div>
              <div id="history-list" class="list"></div>
            </section>
          </main>
        </div>

        <script>
          const state = { latest: null, metadata: null };
          const byId = (id) => document.getElementById(id);
          const escapeHtml = (value) => String(value ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');

          document.querySelectorAll('.nav button').forEach((button) => {
            button.addEventListener('click', () => {
              document.querySelectorAll('.nav button').forEach((item) => item.classList.remove('active'));
              document.querySelectorAll('.screen').forEach((item) => item.classList.remove('active'));
              button.classList.add('active');
              byId(button.dataset.tab).classList.add('active');
            });
          });

          async function getJson(url, options) {
            const response = await fetch(url, options);
            if (!response.ok) {
              if (response.status === 401) {
                await loginFlow();
                return getJson(url, options);
              }
              const text = await response.text();
              throw new Error(`${response.status} ${text}`);
            }
            return response.json();
          }

          async function loginFlow() {
            const status = await fetch('/auth/status').then((response) => response.json());
            if (!status.auth_enabled || status.authenticated) return;
            const username = window.prompt('Username');
            const password = window.prompt('Password');
            if (!username || !password) throw new Error('Login required');
            const response = await fetch('/auth/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username, password })
            });
            if (!response.ok) throw new Error('Login failed');
          }

          async function refreshHealth() {
            try {
              const data = await getJson('/health');
              byId('health-dot').classList.add('ok');
              byId('health-text').textContent = `${data.app}: ok`;
            } catch (error) {
              byId('health-dot').classList.remove('ok');
              byId('health-text').textContent = 'offline';
            }
          }

          function renderSettings(metadata) {
            const rows = [
              ['Environment', metadata.environment],
              ['Quality Threshold', metadata.quality_threshold],
              ['Auth enabled', metadata.auth.enabled ? 'yes' : 'no'],
              ['Postgres DSN configured', metadata.memory.postgres_dsn_configured ? 'yes' : 'no'],
              ['Postgres Checkpointer', metadata.memory.postgres_checkpointer_enabled ? 'enabled' : 'disabled'],
              ['Postgres Archive', metadata.memory.postgres_archive_available ? 'available' : 'fallback'],
              ['Qdrant URL', metadata.memory.qdrant_url],
              ['Qdrant Memory', metadata.memory.qdrant_available ? 'available' : 'fallback'],
              ['Project Memory Collection', metadata.memory.project_memory_collection],
              ['Global Memory Collection', metadata.memory.global_memory_collection],
              ['LLM Provider', metadata.llm.provider],
              ['LLM Model', metadata.llm.model],
              ['LLM Base URL', metadata.llm.base_url],
              ['LLM configured', metadata.llm.configured ? 'yes' : 'no'],
              ['OpenAI API Key', metadata.secrets.openai_api_key_set ? 'set' : 'not set'],
              ['Anthropic API Key', metadata.secrets.anthropic_api_key_set ? 'set' : 'not set'],
              ['LangSmith API Key', metadata.secrets.langsmith_api_key_set ? 'set' : 'not set'],
              ['Where to set keys', metadata.secrets.where_to_set],
            ];
            byId('settings-table').innerHTML = '<tr><th>Setting</th><th>Value</th></tr>' +
              rows.map(([k, v]) => `<tr><td>${escapeHtml(k)}</td><td>${escapeHtml(v)}</td></tr>`).join('');
            byId('memory-info').innerHTML = Object.entries(metadata.paths)
              .map(([key, value]) => `<div class="item"><strong>${escapeHtml(key)}</strong><span class="help">${escapeHtml(value)}</span></div>`)
              .join('');
          }

          function renderIntegrations(integrations) {
            byId('integration-list').innerHTML = Object.entries(integrations).map(([name, value]) => {
              const implemented = value.implemented ? 'implemented' : 'not implemented';
              const configured = value.configured ?? value.installed ?? value.langgraph_json ?? value.url_configured ?? null;
              const detail = configured === null ? '' : `<span class="pill">${configured ? 'ready' : 'needs config'}</span>`;
              return `
                <div class="item">
                  <strong>${escapeHtml(name)}</strong>
                  <span class="pill">${escapeHtml(implemented)}</span>${detail}
                  <div class="help">${escapeHtml(JSON.stringify(value))}</div>
                </div>
              `;
            }).join('');
          }

          function renderMarkdownList(targetId, items) {
            byId(targetId).innerHTML = items.map((item) => `
              <div class="item">
                <strong>${escapeHtml(item.filename)}</strong>
                <div class="help">${escapeHtml(item.content.split('\\n').slice(0, 3).join(' '))}</div>
              </div>
            `).join('');
          }

          function renderBuild(result) {
            state.latest = result;
            byId('metric-score').textContent = `${result.quality_score}/100`;
            byId('metric-status').textContent = result.status;
            byId('metric-artifacts').textContent = result.artifacts.length;
            byId('summary').innerHTML = `<span class="pill">${escapeHtml(result.project_id)}</span><span class="pill">${escapeHtml(result.status)}</span><span class="pill">score ${escapeHtml(result.quality_score)}</span>`;
            byId('output').textContent = JSON.stringify(result, null, 2);
            byId('plan-output').textContent = result.plan || 'Kein Plan vorhanden.';
            byId('artifacts').innerHTML = result.artifacts.map((artifact, index) => `
              <div class="item artifact" data-index="${index}">
                <strong>${escapeHtml(artifact.filename)}</strong>
                <span class="pill">${escapeHtml(artifact.artifact_type)}</span>
                <div class="help">${escapeHtml(artifact.description || '')}</div>
              </div>
            `).join('');
            document.querySelectorAll('.artifact').forEach((item) => {
              item.addEventListener('click', () => {
                const artifact = state.latest.artifacts[Number(item.dataset.index)];
                byId('output').textContent = artifact.content;
              });
            });
          }

          async function runBuild() {
            const button = byId('run-build');
            button.disabled = true;
            byId('output').textContent = 'Build laeuft...';
            try {
              const request = `${byId('request').value}\\n\\nDeployment target: ${byId('target').value}\\nQuality threshold: ${byId('quality').value}`;
              const payload = { user_request: request };
              if (byId('project-id').value.trim()) payload.project_id = byId('project-id').value.trim();
              const result = await getJson('/build', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
              });
              renderBuild(result);
              await refreshHistory();
            } catch (error) {
              byId('output').textContent = error.message;
            } finally {
              button.disabled = false;
            }
          }

          async function refreshHistory() {
            const builds = await getJson('/builds');
            byId('metric-builds').textContent = builds.length;
            byId('history-list').innerHTML = builds.length ? builds.map((item) => `
              <div class="item">
                <strong>${escapeHtml(item.project_id)}</strong>
                <span class="pill">${escapeHtml(item.status)}</span><span class="pill">${escapeHtml(item.quality_score)}/100</span>
                <div class="help">${escapeHtml(item.artifacts.length)} artifacts</div>
              </div>
            `).join('') : '<div class="item">Noch keine Builds.</div>';
          }

          function currentProjectId() {
            return byId('chat-project').value.trim()
              || byId('project-id').value.trim()
              || (state.latest && state.latest.project_id)
              || 'default';
          }

          async function saveChat() {
            const content = byId('chat-content').value.trim();
            if (!content) return;
            const response = await getJson('/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ project_id: currentProjectId(), role: 'user', content })
            });
            byId('chat-content').value = '';
            await loadChat();
            byId('output').textContent = JSON.stringify(response, null, 2);
          }

          async function loadChat() {
            const data = await getJson(`/chat/${encodeURIComponent(currentProjectId())}`);
            byId('chat-list').innerHTML = data.messages.length ? data.messages.map((item) => `
              <div class="item">
                <strong>${escapeHtml(item.role)}</strong>
                <div class="help">${escapeHtml(item.content)}</div>
              </div>
            `).join('') : '<div class="item">Keine Chat-History fuer dieses Projekt.</div>';
          }

          async function searchMemory() {
            const query = byId('memory-query').value.trim();
            if (!query) return;
            const data = await getJson('/memory/search', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ project_id: currentProjectId(), query, limit: 5 })
            });
            byId('memory-results').innerHTML = data.results.length ? data.results.map((item) => `
              <div class="item">
                <strong>score ${Number(item.score).toFixed(3)}</strong>
                <div class="help">${escapeHtml(item.payload.text || JSON.stringify(item.payload))}</div>
              </div>
            `).join('') : '<div class="item">Keine Treffer.</div>';
          }

          async function runLlm() {
            byId('llm-output').textContent = 'LLM laeuft...';
            try {
              const data = await getJson('/llm/complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: byId('llm-prompt').value })
              });
              byId('llm-output').textContent = data.content;
            } catch (error) {
              byId('llm-output').textContent = error.message;
            }
          }

          async function boot() {
            await refreshHealth();
            state.metadata = await getJson('/metadata');
            renderSettings(state.metadata);
            renderIntegrations(state.metadata.integrations);
            const agents = await getJson('/agents');
            renderMarkdownList('agent-list', agents.agents);
            const templates = await getJson('/templates');
            renderMarkdownList('template-list', templates.templates);
            await refreshHistory();
          }

          byId('run-build').addEventListener('click', runBuild);
          byId('save-chat').addEventListener('click', saveChat);
          byId('load-chat').addEventListener('click', loadChat);
          byId('search-memory').addEventListener('click', searchMemory);
          byId('run-llm').addEventListener('click', runLlm);
          byId('load-example').addEventListener('click', () => {
            byId('project-id').value = 'langgraph-builder-production';
            byId('target').value = 'vps';
            byId('request').value = 'Baue ein production-ready LangGraph Builder Team mit Agentenverwaltung, Memory, Archiv, Settings, Chat History, Verification, Deployment und Monitoring.';
          });
          byId('clear-output').addEventListener('click', () => {
            byId('output').textContent = 'Bereit.';
            byId('plan-output').textContent = 'Kein Plan vorhanden.';
            byId('artifacts').innerHTML = '';
          });

          boot();
          setInterval(refreshHealth, 15000);
        </script>
      </body>
    </html>
    """


@app.post("/build", response_model=BuildResponse)
def build(request_payload: BuildRequest, request: Request) -> BuildResponse:
    require_auth(request)
    response = _build_response(request_payload)
    _remember_build(response)
    return response
