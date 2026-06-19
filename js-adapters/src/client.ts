export type BuildRequest = {
  user_request: string;
  project_id?: string;
};

export type BuilderClientOptions = {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
};

export class BuilderClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: BuilderClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? process.env.BUILDER_API_URL ?? "http://localhost:8000";
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async build(input: BuildRequest): Promise<unknown> {
    const response = await this.fetchImpl(`${this.baseUrl}/build`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input)
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  async searchMemory(query: string, projectId?: string): Promise<unknown> {
    const response = await this.fetchImpl(`${this.baseUrl}/memory/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, project_id: projectId })
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }
}
