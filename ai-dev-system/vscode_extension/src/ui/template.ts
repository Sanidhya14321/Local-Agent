export function getWebviewHtml(webviewNonce: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${webviewNonce}';" />
  <title>AI Dev System</title>
  <style>
    :root {
      --bg: var(--vscode-sideBar-background);
      --panel: var(--vscode-editor-background);
      --soft: color-mix(in srgb, var(--vscode-editor-background) 85%, var(--vscode-sideBar-background));
      --text: var(--vscode-foreground);
      --muted: var(--vscode-descriptionForeground);
      --line: var(--vscode-panel-border);
      --accent: var(--vscode-textLink-foreground);
      --ok: var(--vscode-testing-iconPassed);
      --error: var(--vscode-testing-iconFailed);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Ubuntu", sans-serif;
      background: radial-gradient(circle at 100% -10%, color-mix(in srgb, var(--accent) 16%, transparent), transparent 40%), var(--bg);
      color: var(--text);
      height: 100vh;
      overflow: hidden;
    }
    .app {
      height: 100%;
      display: grid;
      grid-template-rows: auto 1fr auto;
    }
    .header {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel) 86%, transparent);
      backdrop-filter: blur(6px);
    }
    .title {
      margin: 0;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .statusline {
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
    }
    .workspace {
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      min-height: 0;
    }
    .chat {
      border-right: 1px solid var(--line);
      min-height: 0;
      display: grid;
      grid-template-rows: 1fr;
    }
    .timeline {
      overflow: auto;
      padding: 14px;
      display: grid;
      gap: 10px;
    }
    .bubble {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: var(--panel);
      font-size: 12px;
      white-space: pre-wrap;
    }
    .bubble.user {
      background: color-mix(in srgb, var(--accent) 12%, var(--panel));
    }
    .bubble.system {
      background: color-mix(in srgb, var(--soft) 88%, transparent);
    }
    .inspector {
      min-height: 0;
      display: grid;
      grid-template-rows: auto auto 1fr auto;
      background: var(--soft);
    }
    .section-title {
      margin: 0;
      padding: 10px 12px;
      font-size: 12px;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .files {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      max-height: 140px;
      overflow: auto;
      font-family: "Cascadia Code", "Consolas", monospace;
      font-size: 11px;
      white-space: pre-wrap;
    }
    .diffs {
      overflow: auto;
      padding: 10px 12px;
      display: grid;
      gap: 10px;
    }
    .diff-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--panel);
    }
    .diff-head {
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      font-size: 11px;
      color: var(--muted);
      font-family: "Cascadia Code", "Consolas", monospace;
    }
    .diff-body {
      margin: 0;
      padding: 10px;
      overflow: auto;
      max-height: 220px;
      font-size: 11px;
      line-height: 1.45;
      font-family: "Cascadia Code", "Consolas", monospace;
      white-space: pre;
    }
    .debug {
      border-top: 1px solid var(--line);
      margin: 0;
      padding: 8px 10px;
      max-height: 140px;
      overflow: auto;
      font-size: 11px;
      line-height: 1.4;
      font-family: "Cascadia Code", "Consolas", monospace;
      background: color-mix(in srgb, var(--panel) 92%, transparent);
      white-space: pre-wrap;
    }
    .composer {
      border-top: 1px solid var(--line);
      padding: 10px;
      display: grid;
      gap: 8px;
      background: var(--panel);
    }
    .input {
      width: 100%;
      min-height: 74px;
      max-height: 180px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      color: var(--text);
      background: var(--bg);
      font-family: inherit;
      font-size: 12px;
    }
    .actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    button {
      border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--line));
      background: color-mix(in srgb, var(--accent) 16%, var(--panel));
      color: var(--text);
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
    }
    button:hover { filter: brightness(1.05); }
    button:disabled { opacity: 0.55; cursor: not-allowed; }
    .tagrow {
      display: flex;
      gap: 8px;
      font-size: 11px;
      color: var(--muted);
      overflow: auto;
      white-space: nowrap;
    }
    .tag {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 8px;
      background: var(--soft);
    }
    .ok { color: var(--ok); }
    .error { color: var(--error); }
    @media (max-width: 860px) {
      .workspace { grid-template-columns: 1fr; }
      .chat { border-right: 0; border-bottom: 1px solid var(--line); }
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="header">
      <h1 class="title">AI Dev System</h1>
      <div id="status" class="statusline">Status: idle</div>
    </div>

    <div class="workspace">
      <section class="chat">
        <div id="timeline" class="timeline"></div>
      </section>

      <section class="inspector">
        <h2 class="section-title">Changed Files</h2>
        <div id="files" class="files">No changes yet</div>
        <div id="diffs" class="diffs"></div>
        <pre id="debug" class="debug">Debug console ready.</pre>
      </section>
    </div>

    <div class="composer">
      <textarea id="task" class="input" placeholder="Ask like Copilot: Build a SaaS authentication system with FastAPI + Next.js"></textarea>
      <div class="actions">
        <button id="preview">Preview Changes</button>
        <button id="apply" disabled>Apply Preview</button>
        <button id="run">Run Workflow</button>
      </div>
      <div class="tagrow">
        <span class="tag">Planner</span>
        <span class="tag">Coder</span>
        <span class="tag">Debugger</span>
        <span class="tag">Reflection + Memory</span>
      </div>
    </div>
  </div>

  <script nonce="${webviewNonce}">
    const vscode = acquireVsCodeApi();
    const taskInput = document.getElementById('task');
    const runBtn = document.getElementById('run');
    const previewBtn = document.getElementById('preview');
    const applyBtn = document.getElementById('apply');
    const status = document.getElementById('status');
    const files = document.getElementById('files');
    const diffs = document.getElementById('diffs');
    const timeline = document.getElementById('timeline');
    const debugEl = document.getElementById('debug');

    let latestPreviewChanges = [];
    let latestPreviewTests = [];
    let lastSystemBubbleText = '';
    let runWatchdog = null;
    let heartbeatTimer = null;
    let currentRunId = '';

    function addBubble(role, text) {
      if (role === 'system' && text === lastSystemBubbleText) {
        return;
      }
      const el = document.createElement('div');
      el.className = 'bubble ' + role;
      el.textContent = text;
      timeline.appendChild(el);
      timeline.scrollTop = timeline.scrollHeight;
      if (role === 'system') {
        lastSystemBubbleText = text;
      }
    }

    function setStatus(text, className) {
      status.textContent = text;
      status.className = 'statusline ' + (className || '');
    }

    function startHeartbeat() {
      stopHeartbeat();
      let dots = 0;
      heartbeatTimer = setInterval(() => {
        dots = (dots + 1) % 4;
        const suffix = '.'.repeat(dots);
        setStatus('Status: running' + suffix + (currentRunId ? ' | run_id: ' + currentRunId : ''), '');
      }, 800);
    }

    function stopHeartbeat() {
      if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
      }
    }

    function appendDebug(text) {
      const stamp = new Date().toLocaleTimeString();
      debugEl.textContent += '\n[' + stamp + '] ' + text;
      debugEl.scrollTop = debugEl.scrollHeight;
    }

    function renderDiffs(changes) {
      diffs.innerHTML = '';
      if (!changes || !changes.length) {
        const empty = document.createElement('div');
        empty.className = 'bubble system';
        empty.textContent = 'No diff preview available yet.';
        diffs.appendChild(empty);
        return;
      }

      changes.forEach((change) => {
        const card = document.createElement('div');
        card.className = 'diff-card';

        const head = document.createElement('div');
        head.className = 'diff-head';
        head.textContent = change.path;

        const body = document.createElement('pre');
        body.className = 'diff-body';
        body.textContent = change.diff || ('New content:\n' + (change.content || ''));

        card.appendChild(head);
        card.appendChild(body);
        diffs.appendChild(card);
      });
    }

    runBtn.addEventListener('click', () => {
      const task = taskInput.value.trim();
      if (!task) {
        setStatus('Status: please enter a task', 'error');
        return;
      }
      addBubble('user', task);
      runBtn.disabled = true;
      runBtn.textContent = 'Running...';
      setStatus('Status: queued', '');
      vscode.postMessage({ type: 'runTask', task });
      appendDebug('Run clicked. Dispatching runTask to extension host.');
      if (runWatchdog) {
        clearTimeout(runWatchdog);
      }
      runWatchdog = setTimeout(() => {
        setStatus('Status: no response from extension host yet', 'error');
        appendDebug('No ack/workflow event within 5s. Check Extension Host logs and ensure extension was rebuilt/reloaded.');
      }, 5000);
    });

    previewBtn.addEventListener('click', () => {
      const task = taskInput.value.trim();
      if (!task) {
        setStatus('Status: please enter a task', 'error');
        return;
      }
      addBubble('user', 'Preview request: ' + task);
      previewBtn.disabled = true;
      previewBtn.textContent = 'Previewing...';
      setStatus('Status: generating preview', '');
      vscode.postMessage({ type: 'previewTask', task });
      appendDebug('Preview clicked. Dispatching previewTask to extension host.');
    });

    applyBtn.addEventListener('click', () => {
      if (!latestPreviewChanges.length) {
        setStatus('Status: no preview changes to apply', 'error');
        return;
      }
      applyBtn.disabled = true;
      applyBtn.textContent = 'Applying...';
      setStatus('Status: applying preview changes', '');
      vscode.postMessage({ type: 'applyPreview', changes: latestPreviewChanges, tests: latestPreviewTests });
      appendDebug('Apply clicked. Dispatching applyPreview to extension host.');
    });

    window.addEventListener('message', (event) => {
      const msg = event.data;

      if (msg.type === 'workflowState') {
        if (runWatchdog) {
          clearTimeout(runWatchdog);
          runWatchdog = null;
        }
        appendDebug('Workflow state update: ' + msg.status + ' (attempt ' + msg.attempts + ')');
        if (msg.status === 'running') {
          startHeartbeat();
        }
        if (msg.status !== 'running') {
          stopHeartbeat();
        }
        setStatus(
          'Status: ' + msg.status + ' (attempts: ' + msg.attempts + ')' + (currentRunId ? ' | run_id: ' + currentRunId : ''),
          msg.status === 'failed' ? 'error' : (msg.status === 'success' ? 'ok' : '')
        );
        files.textContent = (msg.changed_files || []).join('\n') || 'No changes yet';
        addBubble('system', (msg.logs || []).slice(-1)[0] || 'Agent update received');
        if (msg.status === 'success' || msg.status === 'failed') {
          stopHeartbeat();
          runBtn.disabled = false;
          runBtn.textContent = 'Run Workflow';
        }
      }

      if (msg.type === 'previewResult') {
        appendDebug('Preview result received with ' + (msg.changes || []).length + ' change(s).');
        latestPreviewChanges = msg.changes || [];
        latestPreviewTests = msg.tests || [];
        const changePaths = latestPreviewChanges.map((c) => c.path);
        files.textContent = changePaths.join('\n') || 'No proposed file changes';
        renderDiffs(latestPreviewChanges);
        setStatus('Status: preview ready', 'ok');
        addBubble('system', 'Preview generated for ' + changePaths.length + ' file(s).');
        previewBtn.disabled = false;
        previewBtn.textContent = 'Preview Changes';
        applyBtn.disabled = changePaths.length === 0;
        applyBtn.textContent = 'Apply Preview';
      }

      if (msg.type === 'applyResult') {
        appendDebug('Apply result received. Exit code: ' + Number((msg.checks || {}).exit_code));
        const ok = Number((msg.checks || {}).exit_code) === 0;
        const stdout = msg.checks && msg.checks.stdout ? msg.checks.stdout : '';
        const stderr = msg.checks && msg.checks.stderr ? msg.checks.stderr : '';
        setStatus(ok ? 'Status: preview changes applied successfully' : 'Status: applied, checks failed', ok ? 'ok' : 'error');
        files.textContent = (msg.changed_files || []).join('\n') || 'No files applied';
        addBubble('system', 'Applied files: ' + msg.applied + '\n\nCheck stdout:\n' + stdout + '\n\nCheck stderr:\n' + stderr);
        applyBtn.disabled = false;
        applyBtn.textContent = 'Apply Preview';
      }

      if (msg.type === 'error') {
        stopHeartbeat();
        if (runWatchdog) {
          clearTimeout(runWatchdog);
          runWatchdog = null;
        }
        appendDebug('Error received: ' + msg.message);
        setStatus('Status: error (' + msg.message + ')', 'error');
        addBubble('system', 'Error: ' + msg.message);
        runBtn.disabled = false;
        runBtn.textContent = 'Run Workflow';
        previewBtn.disabled = false;
        previewBtn.textContent = 'Preview Changes';
        applyBtn.disabled = false;
        applyBtn.textContent = 'Apply Preview';
      }

      if (msg.type === 'debug') {
        appendDebug(msg.message || 'debug event');
      }

      if (msg.type === 'ack') {
        if (runWatchdog) {
          clearTimeout(runWatchdog);
          runWatchdog = null;
        }
        appendDebug('Ack received from extension host for action: ' + (msg.action || 'unknown'));
      }

      if (msg.type === 'runStarted') {
        currentRunId = String(msg.runId || '');
        appendDebug('Run started with run_id: ' + currentRunId);
        addBubble('system', 'Run started: ' + currentRunId);
        startHeartbeat();
      }
    });
  </script>
</body>
</html>`;
}
