import * as vscode from 'vscode';
import WebSocket from 'ws';
import { ApplyPreviewResponse, McpClient, PreviewResponse, WorkflowState } from './mcp_client';
import { getWebviewHtml } from './ui/template';

export class ChatProvider {
  private panel: vscode.WebviewPanel | undefined;
  private readonly mcpClient: McpClient;
  private readonly output: vscode.OutputChannel;

  constructor(private readonly context: vscode.ExtensionContext) {
    this.mcpClient = new McpClient(context);
    this.output = vscode.window.createOutputChannel('AI Dev System');
    this.context.subscriptions.push(this.output);
  }

  show() {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.Beside);
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      'aiDevSystemPanel',
      'AI Dev System',
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );

    this.panel.webview.html = getWebviewHtml(this.nonce());
    this.panel.onDidDispose(() => {
      this.panel = undefined;
    });

    this.panel.webview.onDidReceiveMessage((msg) => {
      if (msg.type === 'runTask') {
        this.panel?.webview.postMessage({ type: 'ack', action: 'runTask' });
        this.output.appendLine('[ui] received runTask message');
        void this.runAndStream(String(msg.task || '')).catch((error) => {
          const message = error instanceof Error ? error.message : String(error);
          this.output.appendLine(`[runTask] ${message}`);
          this.panel?.webview.postMessage({ type: 'error', message });
        });
      }
      if (msg.type === 'previewTask') {
        this.panel?.webview.postMessage({ type: 'ack', action: 'previewTask' });
        this.output.appendLine('[ui] received previewTask message');
        void this.previewTask(String(msg.task || '')).catch((error) => {
          const message = error instanceof Error ? error.message : String(error);
          this.output.appendLine(`[previewTask] ${message}`);
          this.panel?.webview.postMessage({ type: 'error', message });
        });
      }
      if (msg.type === 'applyPreview') {
        this.panel?.webview.postMessage({ type: 'ack', action: 'applyPreview' });
        this.output.appendLine('[ui] received applyPreview message');
        void this.applyPreview(msg.changes || [], msg.tests || []).catch((error) => {
          const message = error instanceof Error ? error.message : String(error);
          this.output.appendLine(`[applyPreview] ${message}`);
          this.panel?.webview.postMessage({ type: 'error', message });
        });
      }
    });
  }

  async runTaskFromCommand(task: string): Promise<void> {
    this.show();
    await this.runAndStream(task);
  }

  private async runAndStream(task: string): Promise<void> {
    if (!this.panel) {
      return;
    }

    try {
      this.output.appendLine(`[runAndStream] starting task: ${task}`);
      this.panel.webview.postMessage({ type: 'debug', message: `Starting workflow for task: ${task}` });
      const started = await this.mcpClient.startWorkflow(task);
      this.output.appendLine(`[runAndStream] run_id=${started.run_id}`);
      this.panel.webview.postMessage({ type: 'runStarted', runId: started.run_id });
      this.panel.webview.postMessage({ type: 'debug', message: `Workflow created with run_id: ${started.run_id}` });
      const streamed = await this.consumeWebSocketStream(started.run_id);
      if (!streamed) {
        this.output.appendLine('[runAndStream] websocket unavailable or incomplete, falling back to polling');
        this.panel.webview.postMessage({ type: 'debug', message: 'WebSocket stream unavailable, using polling fallback.' });
        await this.pollUntilComplete(started.run_id);
      }
    } catch (error) {
      const message = error instanceof Error ? (error.stack || error.message) : String(error);
      this.output.appendLine(`[runAndStream] error: ${message}`);
      this.panel.webview.postMessage({ type: 'error', message });
      void vscode.window.showErrorMessage(`AI Dev System error: ${message}`);
    }
  }

  private async consumeWebSocketStream(runId: string): Promise<boolean> {
    const streamUrl = this.mcpClient.streamUrl(runId);

    return new Promise<boolean>((resolve) => {
      let settled = false;
      let receivedAnyState = false;
      let terminalSeen = false;
      const settle = (value: boolean) => {
        if (!settled) {
          settled = true;
          resolve(value);
        }
      };

      try {
        const ws = new WebSocket(streamUrl);
        this.output.appendLine(`[ws] connecting ${streamUrl}`);

        ws.on('open', () => {
          this.output.appendLine('[ws] connected');
        });

        ws.on('message', (raw) => {
          try {
            const parsed = JSON.parse(raw.toString()) as WorkflowState;
            if (parsed.status) {
              receivedAnyState = true;
              this.panel?.webview.postMessage({ type: 'workflowState', ...parsed });
              if (this.mcpClient.isTerminalStatus(parsed.status)) {
                terminalSeen = true;
                if (parsed.status === 'failed' && parsed.last_error) {
                  void vscode.window.showErrorMessage(`AI Dev workflow failed: ${parsed.last_error.slice(0, 250)}`);
                }
                ws.close();
                settle(true);
              }
            }
          } catch {
            this.output.appendLine('[ws] ignored malformed frame');
          }
        });

        ws.on('error', (event) => {
          this.output.appendLine(`[ws] error: ${String(event)}`);
          this.panel?.webview.postMessage({ type: 'debug', message: `WebSocket error: ${String(event)}` });
          settle(false);
        });

        ws.on('close', () => {
          this.output.appendLine('[ws] closed');
          settle(terminalSeen && receivedAnyState);
        });

        setTimeout(() => {
          if (ws.readyState !== WebSocket.OPEN && ws.readyState !== WebSocket.CLOSED) {
            try {
              ws.terminate();
            } catch {
              // ignore terminate errors
            }
            settle(false);
          }
        }, 3000);

        setTimeout(() => {
          if (!terminalSeen && !settled) {
            this.output.appendLine('[ws] no terminal status seen yet, switching to polling');
            try {
              ws.close();
            } catch {
              // ignore close errors
            }
            settle(false);
          }
        }, 8000);
      } catch {
        settle(false);
      }
    });
  }

  private async pollUntilComplete(runId: string): Promise<void> {
    const pollMs = Number(vscode.workspace.getConfiguration('aiDevSystem').get('pollIntervalMs', 1500));
    let done = false;

    while (!done) {
      let state: WorkflowState;
      try {
        state = await this.mcpClient.getWorkflow(runId);
        this.panel?.webview.postMessage({
          type: 'debug',
          message: `Polling heartbeat: status=${state.status}, attempts=${state.attempts}`
        });
      } catch (error) {
        const message = error instanceof Error ? (error.stack || error.message) : String(error);
        this.panel?.webview.postMessage({ type: 'error', message: `Polling failed: ${message}` });
        throw error;
      }
      this.panel?.webview.postMessage({ type: 'workflowState', ...state });

      if (this.mcpClient.isTerminalStatus(state.status)) {
        done = true;
        if (state.status === 'failed' && state.last_error) {
          void vscode.window.showErrorMessage(`AI Dev workflow failed: ${state.last_error.slice(0, 250)}`);
        }
      } else {
        await new Promise((resolve) => setTimeout(resolve, pollMs));
      }
    }
  }

  private async previewTask(task: string): Promise<void> {
    if (!this.panel) {
      return;
    }
    this.output.appendLine(`[previewTask] generating preview for: ${task}`);
    this.panel.webview.postMessage({ type: 'debug', message: `Generating preview for: ${task}` });
    const preview: PreviewResponse = await this.mcpClient.previewWorkflow(task);
    this.panel.webview.postMessage({
      type: 'previewResult',
      summary: preview.summary,
      architecture: preview.architecture,
      changes: preview.changes,
      tests: preview.tests
    });
  }

  private async applyPreview(changes: Array<{ path: string; content: string }>, tests: string[]): Promise<void> {
    if (!this.panel) {
      return;
    }
    this.output.appendLine(`[applyPreview] applying ${changes.length} file(s)`);
    this.panel.webview.postMessage({ type: 'debug', message: `Applying ${changes.length} previewed file(s)` });
    const result: ApplyPreviewResponse = await this.mcpClient.applyPreview(changes, tests);
    this.panel.webview.postMessage({
      type: 'applyResult',
      applied: result.applied,
      changed_files: result.changed_files,
      checks: result.checks
    });
  }

  private nonce(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let output = '';
    for (let i = 0; i < 32; i += 1) {
      output += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return output;
  }
}
