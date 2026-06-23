export type TaskStatus = "pending" | "running" | "success" | "failed" | "cancelled";

export interface TaskStep {
  key: string;
  name: string;
  type: string;
  status: TaskStatus;
  order: number;
  started_at: string | null;
  finished_at: string | null;
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  error: string | null;
  retry_count: number;
  config: Record<string, unknown>;
}

export interface Task {
  id: string;
  title: string;
  pipeline_id: string;
  pipeline_name?: string;
  status: TaskStatus;
  progress: number;
  steps: TaskStep[];
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  finished_at: string | null;
}

export interface PipelineStep {
  key: string;
  name: string;
  type: string;
  enabled: boolean;
  order: number;
  config: Record<string, unknown>;
}

export interface Pipeline {
  id: string;
  name: string;
  description: string;
  steps: PipelineStep[];
  created_at: string;
  updated_at: string;
}

export interface Article {
  id: string;
  task_id: string;
  title: string;
  content: Record<string, unknown>;
  html_content: string;
  metadata: Record<string, unknown>;
  images: Image[];
  validation: ValidationResponse | null;
  created_at: string;
  updated_at: string;
}

export interface Image {
  id: string;
  url: string;
  alt: string;
  width: number;
  height: number;
}

export interface Prompt {
  id: string;
  name: string;
  category: string;
  content: string;
  variables: string[];
  version: number;
  versions: PromptVersion[];
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  version: number;
  content: string;
  created_at: string;
}

export interface LLMConfig {
  id: string;
  name: string;
  provider: string;
  model: string;
  api_key_set: boolean;
  temperature: number;
  max_tokens: number;
  created_at: string;
}

export interface SourceBundle {
  id: string;
  task_id: string;
  sources: SourceItem[];
  created_at: string;
}

export interface SourceItem {
  type: string;
  url: string;
  title: string;
  content: string;
  fetched_at: string;
}

export interface ExecutionLog {
  id: string;
  task_id: string;
  step_key: string;
  level: "debug" | "info" | "warning" | "error";
  message: string;
  data: Record<string, unknown> | null;
  created_at: string;
}

export interface WechatPublication {
  id: string;
  article_id: string;
  media_id: string;
  published_at: string | null;
  status: "draft" | "published" | "failed";
  error: string | null;
}

export interface ValidationResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  file_path: string;
  created_at: string;
}

export interface TaskEvent {
  type: "task_updated" | "step_started" | "step_completed" | "step_failed" | "task_completed" | "task_failed";
  task_id: string;
  step_key?: string;
  data: Record<string, unknown>;
  timestamp: string;
}
