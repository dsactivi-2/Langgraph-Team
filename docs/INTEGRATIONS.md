# Integrations

Diese Datei beschreibt die eingebauten Adapter und die Grenzen der jeweiligen
Integration.

## Python Core

| Integration | Datei / Endpoint | Zweck |
| --- | --- | --- |
| LangChain | `src/langgraph_builder_team/langchain_adapter.py` | Builder als `RunnableLambda` und `StructuredTool` nutzen |
| LangGraph | `src/langgraph_builder_team/graph.py` | Primaerer Python `StateGraph` Workflow |
| LangGraph Server | `langgraph.json` | Lokaler Start per `langgraph dev`, sobald die LangGraph CLI installiert ist |
| MCP Adapters | `src/langgraph_builder_team/mcp_adapters.py`, `/mcp/tools` | Externe MCP Tools ueber `langchain-mcp-adapters` laden |
| Agent Protocol | `/agent-protocol/info`, `/agent-protocol/threads`, `/agent-protocol/runs` | Thread-/Run-kompatible API-Flaeche fuer externe Agent Clients |
| Deep Agents | `src/langgraph_builder_team/deep_agents_adapter.py` | Starter-Code fuer einen Deep Agent mit Builder Tool |
| Open SWE | `/integrations/open-swe/task` | Coding-Task als Handoff-Payload exportieren |
| LangConnect | `/integrations/langconnect/query` | Externes LangConnect/RAG Backend abfragen, wenn `LANGCONNECT_URL` gesetzt ist |

## JavaScript / TypeScript

Das Paket unter `js-adapters/` stellt Adapter fuer Node-basierte Clients bereit:

- `src/client.ts`: HTTP Client gegen die Python API
- `src/langchain.ts`: LangChain.js Tool
- `src/langgraph.ts`: LangGraph.js Wrapper-Graph
- `src/deep-agents.ts`: Deep Agents.js Starter

Installation:

```bash
cd js-adapters
npm install
npm run typecheck
```

## LangSmith

LangSmith wird env-gesteuert vorbereitet:

```bash
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT="LangGraph Builder Team"
```

## MCP Server Konfiguration

`MCP_SERVERS_JSON` akzeptiert JSON im Format, das in
`langchain-mcp-adapters` in eine `MultiServerMCPClient` Konfiguration uebersetzt
wird.

Beispiel:

```json
{
  "filesystem": {
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
  }
}
```

## Noch bewusst getrennt

Open SWE, LangConnect und Slack sind externe Systeme. Dieses Repository enthaelt
die Adapter-/Handoff-Punkte, aber startet diese Systeme nicht selbst. Das haelt
den Core deploybar und verhindert, dass ein einzelnes Docker Compose Setup zu
viele Verantwortlichkeiten uebernimmt.
