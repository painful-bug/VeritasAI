#!/bin/bash
git add .
git commit -m $1
npm run compile && code --install-extension ./vscode-extension/ai-ethics-compliance-agent-0.1.0.vsix