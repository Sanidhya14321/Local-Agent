import * as vscode from 'vscode';

export interface WorkflowStartResponse {
  run_id: string;
  status: string;
}

export interface WorkflowState {
  run_id: string;
  status: 'queued' | 'running' | 'success' | 'failed';
  task: string;
  logs: string[];
  changed_files: string[];
  attempts: number;
  last_error: string;
}

export interface PreviewResponse {
  task: string;
  summary: string;
  architecture: Record<string, string[]>;
  changes: Array<{ path: string; content: string; before_content?: string; diff?: string }>;
  tests: string[];
}

export interface ApplyPreviewResponse {
  applied: number;
  changed_files: string[];
  checks: { exit_code: number; stdout: string; stderr: string };
}

export class McpClient {
  constructor(private readonly context: vscode.ExtensionContext) {}

  private baseUrl(): string {
    const cfg = vscode.workspace.getConfiguration('aiDevSystem');
    return String(cfg.get('serverUrl', 'http://127.0.0.1:8765')).replace(/\/$/, '');
  }

  private requestTimeoutMs(): number {
    const cfg = vscode.workspace.getConfiguration('aiDevSystem');
    return Number(cfg.get('requestTimeoutMs', 20000));
  }

  private async fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeoutMs());
    try {
      const resp = await fetch(url, { ...(init || {}), signal: controller.signal });
      if (!resp.ok) {
        throw new Error(`Request failed: ${resp.status} ${resp.statusText}`);
      }
      return (await resp.json()) as T;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Request timed out after ${this.requestTimeoutMs()}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  streamUrl(runId: string): string {
    const base = this.baseUrl();
    if (base.startsWith('https://')) {
      return `${base.replace('https://', 'wss://')}/workflow/${runId}/stream`;
    }
    return `${base.replace('http://', 'ws://')}/workflow/${runId}/stream`;
  }

  isTerminalStatus(status: WorkflowState['status']): boolean {
    return status === 'success' || status === 'failed';
  }

  async health(): Promise<Record<string, string>> {
    return await this.fetchJson<Record<string, string>>(`${this.baseUrl()}/health`);
  }

  async startWorkflow(task: string): Promise<WorkflowStartResponse> {
    return await this.fetchJson<WorkflowStartResponse>(`${this.baseUrl()}/workflow/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task })
    });
  }

  async getWorkflow(runId: string): Promise<WorkflowState> {
    return await this.fetchJson<WorkflowState>(`${this.baseUrl()}/workflow/${runId}`);
  }

  async previewWorkflow(task: string): Promise<PreviewResponse> {
    return await this.fetchJson<PreviewResponse>(`${this.baseUrl()}/workflow/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task })
    });
  }

  async applyPreview(changes: Array<{ path: string; content: string }>, tests: string[]): Promise<ApplyPreviewResponse> {
    return await this.fetchJson<ApplyPreviewResponse>(`${this.baseUrl()}/workflow/preview/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ changes, tests })
    });
  }
}
