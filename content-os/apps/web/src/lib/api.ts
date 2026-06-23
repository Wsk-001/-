import { Task, Pipeline, Article, Prompt, LLMConfig, Template, SourceBundle, ValidationResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || res.statusText);
    }
    return res.json();
  }

  // Tasks
  async getTasks(params?: { status?: string }): Promise<Task[]> {
    const query = params?.status ? `?status=${params.status}` : "";
    return this.request<Task[]>(`/api/tasks${query}`);
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${taskId}`);
  }

  async createTask(data: { pipeline_id: string; inputs: Record<string, unknown>; title: string }): Promise<Task> {
    return this.request<Task>("/api/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async retryTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${taskId}/retry`, { method: "POST" });
  }

  async cancelTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${taskId}/cancel`, { method: "POST" });
  }

  async runStep(taskId: string, stepKey: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${taskId}/steps/${stepKey}/run`, { method: "POST" });
  }

  // Pipelines
  async getPipelines(): Promise<Pipeline[]> {
    return this.request<Pipeline[]>("/api/pipelines");
  }

  async getPipeline(id: string): Promise<Pipeline> {
    return this.request<Pipeline>(`/api/pipelines/${id}`);
  }

  async createPipeline(data: Partial<Pipeline>): Promise<Pipeline> {
    return this.request<Pipeline>("/api/pipelines", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updatePipeline(id: string, data: Partial<Pipeline>): Promise<Pipeline> {
    return this.request<Pipeline>(`/api/pipelines/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async addStep(pipelineId: string, data: Partial<Pipeline["steps"][0]>): Promise<Pipeline> {
    return this.request<Pipeline>(`/api/pipelines/${pipelineId}/steps`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateStep(pipelineId: string, stepKey: string, data: Partial<Pipeline["steps"][0]>): Promise<Pipeline> {
    return this.request<Pipeline>(`/api/pipelines/${pipelineId}/steps/${stepKey}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteStep(pipelineId: string, stepKey: string): Promise<Pipeline> {
    return this.request<Pipeline>(`/api/pipelines/${pipelineId}/steps/${stepKey}`, {
      method: "DELETE",
    });
  }

  // Articles
  async getArticle(id: string): Promise<Article> {
    return this.request<Article>(`/api/articles/${id}`);
  }

  async getArticleHtml(id: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/api/articles/${id}/html`);
    if (!res.ok) throw new Error(res.statusText);
    return res.text();
  }

  async updateArticle(id: string, data: Partial<Article>): Promise<Article> {
    return this.request<Article>(`/api/articles/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async validateArticle(id: string): Promise<ValidationResponse> {
    return this.request<ValidationResponse>(`/api/articles/${id}/validate`, { method: "POST" });
  }

  // Prompts
  async getPrompts(): Promise<Prompt[]> {
    return this.request<Prompt[]>("/api/prompts");
  }

  async createPrompt(data: Partial<Prompt>): Promise<Prompt> {
    return this.request<Prompt>("/api/prompts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updatePrompt(id: string, data: Partial<Prompt>): Promise<Prompt> {
    return this.request<Prompt>(`/api/prompts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async dryRunPrompt(id: string, data: { variables: Record<string, string> }): Promise<{ output: string; tokens_used: number }> {
    return this.request(`/api/prompts/${id}/dry-run`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async renderPrompt(id: string, data: { variables: Record<string, string> }): Promise<{ rendered: string }> {
    return this.request(`/api/prompts/${id}/render`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Sources
  async collectSources(data: { sources: unknown[] }): Promise<SourceBundle> {
    return this.request<SourceBundle>("/api/sources/collect", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // LLM Configs
  async getLlmConfigs(): Promise<LLMConfig[]> {
    return this.request<LLMConfig[]>("/api/llm-configs");
  }

  async createLlmConfig(data: Partial<LLMConfig>): Promise<LLMConfig> {
    return this.request<LLMConfig>("/api/llm-configs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Templates
  async getTemplates(): Promise<Template[]> {
    return this.request<Template[]>("/api/templates");
  }
}

export const api = new ApiClient(API_BASE);
