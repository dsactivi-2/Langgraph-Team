from __future__ import annotations

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from pydantic import TypeAdapter

from .models import BuilderState
from .nodes import (
    agent_builder,
    executor_sandbox_tester,
    git_docs_deployment_specialist,
    memory_skills_designer,
    planner_architect,
    reviewer_critic,
    verifier_evaluator,
)
from .settings import get_settings


def build_builder_graph(checkpointer=None):
    graph = StateGraph(BuilderState)
    graph.add_node("planner", planner_architect)
    graph.add_node("builder", agent_builder)
    graph.add_node("memory", memory_skills_designer)
    graph.add_node("executor", executor_sandbox_tester)
    graph.add_node("reviewer", reviewer_critic)
    graph.add_node("verifier", verifier_evaluator)
    graph.add_node("deployment", git_docs_deployment_specialist)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "builder")
    graph.add_edge("builder", "memory")
    graph.add_edge("memory", "executor")
    graph.add_edge("executor", "reviewer")
    graph.add_edge("reviewer", "verifier")
    graph.add_edge("verifier", "deployment")
    graph.add_edge("deployment", END)
    return graph.compile(checkpointer=checkpointer)


def run_build(user_request: str, project_id: str | None = None) -> BuilderState:
    user_request = user_request.strip()
    if not user_request:
        raise ValueError("user_request must not be empty")
    kwargs = {"user_request": user_request}
    if project_id:
        kwargs["project_id"] = project_id.strip()
    initial_state = BuilderState(**kwargs)
    settings = get_settings()
    config = {"configurable": {"thread_id": initial_state.project_id}}
    result = None
    if settings.postgres_checkpointer_enabled:
        try:
            with PostgresSaver.from_conn_string(settings.postgres_dsn) as checkpointer:
                checkpointer.setup()
                graph = build_builder_graph(checkpointer=checkpointer)
                result = graph.invoke(initial_state, config=config)
        except Exception as exc:
            initial_state.reflection_notes.append(f"Postgres checkpointer unavailable: {exc}")
    if result is None:
        graph = build_builder_graph()
        result = graph.invoke(initial_state, config=config)
    if isinstance(result, BuilderState):
        return result
    return TypeAdapter(BuilderState).validate_python(result)
