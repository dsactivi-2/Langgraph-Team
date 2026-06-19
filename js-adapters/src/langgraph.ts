import { Annotation, END, START, StateGraph } from "@langchain/langgraph";

import { BuilderClient } from "./client.js";

const BuilderAnnotation = Annotation.Root({
  user_request: Annotation<string>(),
  project_id: Annotation<string | undefined>(),
  result: Annotation<unknown | undefined>()
});

export function createBuilderLangGraph(client = new BuilderClient()) {
  const graph = new StateGraph(BuilderAnnotation) as any;

  graph.addNode("build", async (state: typeof BuilderAnnotation.State) => ({
    result: await client.build({
      user_request: state.user_request,
      project_id: state.project_id
    })
  }));
  graph.addEdge(START, "build");
  graph.addEdge("build", END);
  return graph.compile();
}
