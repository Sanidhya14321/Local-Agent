import * as vscode from 'vscode';
import { ChatProvider } from './chat_provider';

export function registerCommands(context: vscode.ExtensionContext, chatProvider: ChatProvider): void {
  context.subscriptions.push(
    vscode.commands.registerCommand('aiDevSystem.openPanel', () => {
      chatProvider.show();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('aiDevSystem.runTask', async () => {
      const task = await vscode.window.showInputBox({
        prompt: 'Enter the software task to run through local AI agents',
        placeHolder: 'Build a SaaS authentication system with FastAPI + Next.js'
      });

      if (!task?.trim()) {
        return;
      }

      await chatProvider.runTaskFromCommand(task.trim());
    })
  );
}
