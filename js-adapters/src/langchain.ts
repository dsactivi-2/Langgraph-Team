import { DynamicStructuredTool } from "@langchain/core/tools";
import { z } from "zod";

import { BuilderClient } from "./client.js";

export function createBuilderLangChainTool(client = new BuilderClient()) {
  return new DynamicStructuredTool({
    name: "langgraph_builder_team",
    description: "Plan, build, test, review, verify, and package LangGraph projects.",
    schema: z.object({
      user_request: z.string(),
      project_id: z.string().optional()
    }),
    func: async (input) => JSON.stringify(await client.build(input))
  });
}
