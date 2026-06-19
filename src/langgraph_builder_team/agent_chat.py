from __future__ import annotations

from textwrap import dedent
from typing import Any

from .llm import LLMUnavailable, OpenAICompatibleLLM
from .models import AgentChatRequest, BuildRequest, BuildResponse
from .storage import HybridBuildArchive
from .vector_memory import HybridMemory

AGENT_PERSONAS: dict[str, str] = {
    "orchestrator": (
        "koordiniert den naechsten sinnvollen Schritt und haelt den Gesamtstatus im Blick"
    ),
    "planner_architect": "erstellt Architektur, Ziele, Risiken und Umsetzungsplaene",
    "agent_builder": "uebersetzt Anforderungen in LangGraph-Code und Projektartefakte",
    "memory_skills_designer": "plant Memory, RAG, Skills, MCP-Tools und Wissensspeicher",
    "executor_sandbox_tester": (
        "denkt in Tests, Sandbox-Laeufen, Fehlerbildern und Reproduzierbarkeit"
    ),
    "reviewer_critic": "reviewed Code, Architektur, Sicherheit und Production-Risiken streng",
    "verifier_evaluator": "bewertet Quality Gates, Scores und Freigabeentscheidungen",
    "git_docs_deployment_specialist": (
        "kuemmert sich um Git, Dokumentation, Docker, VPS und Deployment"
    ),
}


def _format_memory_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "Keine relevanten Memory-Treffer."
    lines = []
    for item in results[:5]:
        payload = item.get("payload") or {}
        text = str(payload.get("text") or payload)
        lines.append(f"- score={item.get('score', 0):.3f}: {text[:500]}")
    return "\n".join(lines)


def _format_history(messages: list[dict[str, Any]]) -> str:
    if not messages:
        return "Noch keine Chat-History."
    lines = []
    for item in messages[-8:]:
        lines.append(f"{item.get('role', 'unknown')}: {item.get('content', '')[:800]}")
    return "\n".join(lines)


def _fallback_response(
    payload: AgentChatRequest,
    memory_results: list[dict[str, Any]],
    build: BuildResponse | None,
) -> str:
    persona = AGENT_PERSONAS[payload.agent]
    memory_hint = (
        "Ich habe passende Memory-Treffer gefunden und kann daran anknuepfen."
        if memory_results
        else "Ich habe noch keine starken Memory-Treffer fuer diese Anfrage."
    )
    build_hint = ""
    if build:
        build_hint = (
            f"\n\nBuild wurde ausgefuehrt: `{build.project_id}` mit Score "
            f"{build.quality_score}/100 und Status `{build.status}`."
        )
    return dedent(
        f"""
        Ich antworte als `{payload.agent}`.
        Meine Rolle: Ich {persona}.

        Verstanden: {payload.message}

        {memory_hint}

        Sinnvoller naechster Schritt:
        - Wenn du planen willst: Ziel, Scope, Constraints und Erfolgskriterien schaerfen.
        - Wenn du bauen willst: `run_build` aktivieren oder im Build Studio ausfuehren.
        - Wenn du reviewen willst: konkrete Artefakte oder Projekt-ID nennen.
        - Wenn du deployen willst: Environment, Secrets, Domain und VPS-Ziel klaeren.{build_hint}
        """
    ).strip()


def create_agent_chat_reply(
    payload: AgentChatRequest,
    archive: HybridBuildArchive,
    memory: HybridMemory,
    llm: OpenAICompatibleLLM,
    build_runner,
) -> dict[str, Any]:
    user_message = archive.add_chat_message(payload.project_id, "user", payload.message)
    memory.upsert(
        payload.project_id,
        payload.message,
        {"kind": "agent_chat", "role": "user", "agent": payload.agent},
    )

    memory_results = memory.search(payload.message, payload.project_id, 5)
    history = archive.list_chat_messages(payload.project_id)
    build: BuildResponse | None = None
    if payload.run_build:
        build = build_runner(
            BuildRequest(user_request=payload.message, project_id=payload.project_id)
        )

    system = dedent(
        f"""
        Du bist der Agent `{payload.agent}` im LangGraph Builder Team.
        Deine Rolle: {AGENT_PERSONAS[payload.agent]}.
        Antworte konkret, knapp und handlungsorientiert auf Deutsch.
        Nutze Chat-History und Memory-Kontext. Erfinde keine externen Tool-Ergebnisse.
        """
    ).strip()
    prompt = dedent(
        f"""
        User Message:
        {payload.message}

        Chat History:
        {_format_history(history)}

        Memory Treffer:
        {_format_memory_results(memory_results)}

        Build Result:
        {build.model_dump(mode="json") if build else "Kein Build in dieser Nachricht ausgefuehrt."}
        """
    ).strip()

    llm_used = False
    try:
        if payload.use_llm:
            content = llm.complete(prompt, system)
            llm_used = True
        else:
            raise LLMUnavailable("LLM disabled for this request")
    except LLMUnavailable:
        content = _fallback_response(payload, memory_results, build)

    assistant_message = archive.add_chat_message(payload.project_id, "assistant", content)
    memory.upsert(
        payload.project_id,
        content,
        {"kind": "agent_chat", "role": "assistant", "agent": payload.agent},
    )
    return {
        "project_id": payload.project_id,
        "agent": payload.agent,
        "llm_used": llm_used,
        "user_message": user_message,
        "assistant_message": assistant_message,
        "memory_results": memory_results,
        "build": build.model_dump(mode="json") if build else None,
        "storage_error": archive.last_error,
        "qdrant_error": memory.last_error,
    }
