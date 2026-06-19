import { createDeepAgent } from "deepagents";

import { createBuilderLangChainTool } from "./langchain.js";

export function createBuilderDeepAgent(model = process.env.LLM_MODEL ?? "gpt-4o-mini") {
  return createDeepAgent({
    model,
    tools: [createBuilderLangChainTool()],
    systemPrompt: "You are a production LangGraph builder with memory, review, and deployment gates."
  });
}
