from __future__ import annotations

from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .graph import run_build
from .models import BuildRequest, BuildResponse
from .settings import get_settings

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

BUILD_HISTORY: list[BuildResponse] = []
BUILD_HISTORY_LOCK = Lock()
MAX_HISTORY_ITEMS = 25


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
        BUILD_HISTORY.insert(0, response)
        del BUILD_HISTORY[MAX_HISTORY_ITEMS:]


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
def metadata() -> dict[str, object]:
    return {
        "app": settings.app_name,
        "environment": settings.app_env,
        "quality_threshold": settings.quality_threshold,
        "memory": {
            "postgres_dsn_configured": bool(settings.postgres_dsn),
            "qdrant_url": settings.qdrant_url,
            "project_memory_collection": settings.project_memory_collection,
            "global_memory_collection": settings.global_memory_collection,
        },
        "secrets": {
            "openai_api_key_set": bool(settings.openai_api_key),
            "anthropic_api_key_set": bool(settings.anthropic_api_key),
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
def agents() -> dict[str, list[dict[str, str]]]:
    return {"agents": _list_markdown(AGENTS_DIR)}


@app.get("/templates")
def templates() -> dict[str, list[dict[str, str]]]:
    return {"templates": _list_markdown(TEMPLATES_DIR)}


@app.get("/prompts")
def prompts() -> dict[str, list[dict[str, str]]]:
    return {"prompts": _list_markdown(PROMPTS_DIR)}


@app.get("/builds", response_model=list[BuildResponse])
def builds() -> list[BuildResponse]:
    with BUILD_HISTORY_LOCK:
        return list(BUILD_HISTORY)


@app.get("/builds/{project_id}", response_model=BuildResponse)
def build_detail(project_id: str) -> BuildResponse:
    with BUILD_HISTORY_LOCK:
        for item in BUILD_HISTORY:
            if item.project_id == project_id:
                return item
    raise HTTPException(status_code=404, detail="Build not found")


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
                </div>
                <div class="panel">
                  <h2>Archiv</h2>
                  <p class="help">Aktuell wird Build-History im Prozessspeicher gehalten. Fuer Production: Artefakte in Postgres/Object Storage archivieren, nach `project_id` versionieren und Reports in `docs/reports/` exportieren.</p>
                  <div class="pill">docs/reports/</div>
                  <div class="pill">generated_artifacts</div>
                  <div class="pill">project_id namespace</div>
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
              const text = await response.text();
              throw new Error(`${response.status} ${text}`);
            }
            return response.json();
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
              ['Postgres DSN configured', metadata.memory.postgres_dsn_configured ? 'yes' : 'no'],
              ['Qdrant URL', metadata.memory.qdrant_url],
              ['Project Memory Collection', metadata.memory.project_memory_collection],
              ['Global Memory Collection', metadata.memory.global_memory_collection],
              ['OpenAI API Key', metadata.secrets.openai_api_key_set ? 'set' : 'not set'],
              ['Anthropic API Key', metadata.secrets.anthropic_api_key_set ? 'set' : 'not set'],
              ['Where to set keys', metadata.secrets.where_to_set],
            ];
            byId('settings-table').innerHTML = '<tr><th>Setting</th><th>Value</th></tr>' +
              rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join('');
            byId('memory-info').innerHTML = Object.entries(metadata.paths)
              .map(([key, value]) => `<div class="item"><strong>${key}</strong><span class="help">${value}</span></div>`)
              .join('');
          }

          function renderMarkdownList(targetId, items) {
            byId(targetId).innerHTML = items.map((item) => `
              <div class="item">
                <strong>${item.filename}</strong>
                <div class="help">${item.content.split('\\n').slice(0, 3).join(' ')}</div>
              </div>
            `).join('');
          }

          function renderBuild(result) {
            state.latest = result;
            byId('metric-score').textContent = `${result.quality_score}/100`;
            byId('metric-status').textContent = result.status;
            byId('metric-artifacts').textContent = result.artifacts.length;
            byId('summary').innerHTML = `<span class="pill">${result.project_id}</span><span class="pill">${result.status}</span><span class="pill">score ${result.quality_score}</span>`;
            byId('output').textContent = JSON.stringify(result, null, 2);
            byId('plan-output').textContent = result.plan || 'Kein Plan vorhanden.';
            byId('artifacts').innerHTML = result.artifacts.map((artifact, index) => `
              <div class="item artifact" data-index="${index}">
                <strong>${artifact.filename}</strong>
                <span class="pill">${artifact.artifact_type}</span>
                <div class="help">${artifact.description || ''}</div>
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
                <strong>${item.project_id}</strong>
                <span class="pill">${item.status}</span><span class="pill">${item.quality_score}/100</span>
                <div class="help">${item.artifacts.length} artifacts</div>
              </div>
            `).join('') : '<div class="item">Noch keine Builds.</div>';
          }

          async function boot() {
            await refreshHealth();
            state.metadata = await getJson('/metadata');
            renderSettings(state.metadata);
            const agents = await getJson('/agents');
            renderMarkdownList('agent-list', agents.agents);
            const templates = await getJson('/templates');
            renderMarkdownList('template-list', templates.templates);
            await refreshHistory();
          }

          byId('run-build').addEventListener('click', runBuild);
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
def build(request: BuildRequest) -> BuildResponse:
    response = _build_response(request)
    _remember_build(response)
    return response
