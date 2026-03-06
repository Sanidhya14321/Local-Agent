# AI Dev System VS Code Extension

## Commands

- `AI Dev System: Open Panel`
- `AI Dev System: Run Task`

## Flow

1. User enters a task in the panel.
2. Optional: click `Preview Changes` to call `POST /workflow/preview`.
3. Optional: click `Apply Preview` to apply proposed changes through `POST /workflow/preview/apply`.
4. Click `Run Workflow` to execute the full autonomous loop via `POST /workflow/run`.
5. Extension streams updates via WebSocket and falls back to polling if needed.

## Development

```bash
cd vscode_extension
npm install
npm run compile
```

Press `F5` in VS Code to launch extension host.
