#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../vscode_extension"
npm install
npm run compile

echo "Open this folder in VS Code and press F5 to run the extension host"
