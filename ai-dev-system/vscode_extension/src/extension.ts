import * as vscode from 'vscode';
import { ChatProvider } from './chat_provider';
import { registerCommands } from './command_handlers';
import { McpClient } from './mcp_client';

export async function activate(context: vscode.ExtensionContext) {
  const output = vscode.window.createOutputChannel('AI Dev System');
  context.subscriptions.push(output);

  const activatedAt = new Date().toISOString();
  output.appendLine(`[activate] AI Dev System extension activated at ${activatedAt}`);

  const chatProvider = new ChatProvider(context);
  output.appendLine('[activate] Chat provider initialized');
  registerCommands(context, chatProvider);
  output.appendLine('[activate] Commands registered');

  const continueExtension = vscode.extensions.getExtension('Continue.continue');
  if (continueExtension) {
    output.appendLine('[activate] Continue extension detected in host (non-isolated session likely)');
    void vscode.window.showWarningMessage(
      'AI Dev System: Continue is active in this host. Use an isolated launch profile to avoid extension conflicts.'
    );
  }

  const mcpClient = new McpClient(context);
  void (async () => {
    try {
      await mcpClient.health();
      output.appendLine('[health] MCP server reachable');
      void vscode.window.setStatusBarMessage('AI Dev System: MCP server connected', 4000);
    } catch {
      output.appendLine('[health] MCP server unreachable');
      void vscode.window.showWarningMessage(
        'AI Dev System: MCP server is not reachable. Start it with ./scripts/start_mcp.sh from ai-dev-system root.'
      );
    }
  })();

  const diagnosticsCommand = vscode.commands.registerCommand('aiDevSystem.showDiagnostics', async () => {
    const serverUrl = vscode.workspace
      .getConfiguration('aiDevSystem')
      .get<string>('serverUrl', 'http://127.0.0.1:8765');

    output.show(true);
    output.appendLine('[diagnostics] Running extension diagnostics');
    output.appendLine(`[diagnostics] Activated at: ${activatedAt}`);
    output.appendLine(`[diagnostics] Configured server URL: ${serverUrl}`);

    try {
      await mcpClient.health();
      output.appendLine('[diagnostics] MCP health check: OK');
      void vscode.window.showInformationMessage('AI Dev System diagnostics: extension active, MCP reachable.');
    } catch {
      output.appendLine('[diagnostics] MCP health check: FAILED');
      void vscode.window.showWarningMessage(
        'AI Dev System diagnostics: extension active, but MCP is unreachable.'
      );
    }
  });

  context.subscriptions.push(diagnosticsCommand);
}

export function deactivate() {
  // no-op
}
