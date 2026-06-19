from langgraph_builder_team.integrations import integration_matrix
from langgraph_builder_team.langchain_adapter import build_builder_runnable, build_builder_tool
from langgraph_builder_team.mcp_adapters import build_mcp_client_config, parse_mcp_servers


def test_integration_matrix_reports_core_adapters():
    matrix = integration_matrix()

    assert matrix["langchain"]["implemented"] is True
    assert matrix["langgraph"]["implemented"] is True
    assert matrix["mcp_adapters"]["implemented"] is True
    assert matrix["agent_protocol"]["implemented"] is True
    assert matrix["open_swe"]["implemented"] is True


def test_langchain_runnable_invokes_builder():
    runnable = build_builder_runnable()

    result = runnable.invoke(
        {
            "user_request": "Build a test project through LangChain",
            "project_id": "langchain-test",
        }
    )

    assert result["project_id"] == "langchain-test"
    assert result["quality_score"] >= 75


def test_langchain_tool_is_named():
    tool = build_builder_tool()

    assert tool.name == "langgraph_builder_team"


def test_mcp_server_config_parsing():
    servers = parse_mcp_servers(
        '{"filesystem":{"transport":"stdio","command":"npx","args":["server"]}}'
    )

    assert servers[0].name == "filesystem"
    assert build_mcp_client_config(servers)["filesystem"]["command"] == "npx"
