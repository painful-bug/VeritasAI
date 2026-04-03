# Publishing AI Ethics Extension

## Part 1: Publishing Without API Keys

### Step 1: Prepare the Release

```bash
# From the repository root
cd /Users/aishik/Documents/Programming/ethics_agent

# Verify your .env file is NOT staged
git status

# If .env is staged, unstage it
git reset HEAD .env

# Commit all extension and non-sensitive changes
git add vscode-extension/src vscode-extension/package.json vscode-extension/CHANGELOG.md
git add ARCHITECTURE.md README.md
git commit -m "Release v0.x.0: [your summary here]"

# Verify only expected files are staged
git status
```

### Step 2: Build the Extension

```bash
# Navigate to the extension directory
cd vscode-extension

# Compile TypeScript to JavaScript (generates out/)
npm run compile

# Verify the build succeeded
ls -la out/

# Return to repo root
cd ..
```

### Step 3: Install vsce If Needed

```bash
# Install the VS Code packaging tool globally
npm install -g vsce

# Verify installation
vsce --version
```

### Step 4: Package the Extension (No API Keys Included)

```bash
# Navigate to extension directory
cd vscode-extension

# Package into a .vsix file (this bundles only src/, out/, and public assets—NOT .env)
vsce package

# Verify the .vsix was created
ls -la *.vsix

# Optional: Inspect the package contents to confirm no .env
unzip -l ai-ethics-compliance-agent-*.vsix | grep -E "\.env|.langgraph|secrets"
# Should return nothing

# Return to repo root
cd ..
```

### Step 5: Publish to Marketplace

Before publishing, you need to authenticate with a VS Code Marketplace PAT. Choose ONE method:

**Option A: Use vsce login (interactive)**

```bash
# Log in with your Publisher ID (or register at https://marketplace.visualstudio.com/)
vsce login <your-publisher-id>
# Enter your Personal Access Token when prompted (saved locally)
```

**Option B: Use environment variable (non-interactive)**

```bash
# Set your PAT as an environment variable (never commit this)
export VSCE_PAT="your-marketplace-pat-here"

# Verify it's set
echo $VSCE_PAT
```

**Then publish:**

```bash
# Navigate to extension directory
cd vscode-extension

# Publish for the first time (auto-bumps version based on tag)
# Replace <patch|minor|major> with your choice:
#   - patch: 0.1.0 → 0.1.1 (bug fixes)
#   - minor: 0.1.0 → 0.2.0 (new features)
#   - major: 0.1.0 → 1.0.0 (breaking changes)
vsce publish patch

# Or explicitly specify the version
vsce publish 0.1.1

# You should see:
# "Publishing <extension-id> v0.1.1..."
# "✓ Successfully published..."

# Return to repo root
cd ..
```

### Step 6: Create a Git Tag (Recommended)

```bash
# Tag the release for future reference
git tag vscode-0.1.1
git push origin --tags

# Verify the tag exists
git tag -l | grep vscode
```

---

## Part 2: Installing & Configuring the Extension

### Step 1: Install from Marketplace

Once published, the extension appears in VS Code's marketplace. Install it one of two ways:

**Option A: From Command Palette**

```bash
# Open VS Code
code

# In the Command Palette (Ctrl+Shift+P / Cmd+Shift+P):
# Type: Extensions: Install from Marketplace
# Search: "AI Ethics Compliance Agent"
# Click Install
```

**Option B: Direct Installation URL (if you know the publisher ID)**

```bash
# From terminal (if extension is published under publisher "mycompany")
code --install-extension mycompany.ai-ethics-compliance-agent
```

**Option C: Install Local .vsix for Testing**

```bash
# If testing locally before Marketplace publish:
code --install-extension /Users/aishik/Documents/Programming/ethics_agent/vscode-extension/ai-ethics-compliance-agent-0.1.1.vsix
```

### Step 2: Configure Provider & Model

Open VS Code Settings (Cmd+,) and search for `aiEthics`:

```json
{
  "aiEthics.enabled": true,
  "aiEthics.provider": "groq",
  "aiEthics.model": "mixtral-8x7b-32768",
  "aiEthics.debounceMs": 5000
}
```

Available providers:
- `groq`: Groq Cloud (recommended for free tier)
- `openrouter`: OpenRouter multi-model proxy
- `ollama_cloud`: Ollama Cloud hosted models
- `ollama_local`: Local Ollama instance

### Step 3: Supply API Keys (First Run)

When you edit a file, the extension attempts to connect. On first run, it prompts you to set credentials.

**Automatic setup:**
- The extension detects the provider from settings
- On first MCP connection, it prompts: `"AI Ethics: API Key Required"`
- Enter your key; it is stored securely in VS Code's `SecretStorage` (not in .env or the filesystem)

**Manual setup (if needed):**

```bash
# Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
# Command: "AI Ethics: Setup API Credentials"
# Follow the prompts to select provider and enter key
```

**Copy your API key from the correct provider:**

- **Groq**: Visit https://console.groq.com/keys → Copy `GROQ_API_KEY`
- **OpenRouter**: Visit https://openrouter.ai/keys → Copy key
- **Ollama Cloud**: Visit https://ollama.ai/keys → Copy key
- **Ollama Local**: No key required; ensure `ollama serve` is running on `http://localhost:11434`

**Paste the key:**

```
When prompted, paste the entire key (e.g., gsk_XXXXXXXXXXXXXXXXXXXX) and press Enter.
The key is stored securely and never appears in logs or code.
```

### Step 4: Verify Connection

Edit or create a test file (e.g., `test.py`):

```python
# Simple test file
user_age = input("What is your age?")
print(f"You are {user_age} years old")
```

Expected behavior:
- After 5 seconds of inactivity, a scan runs automatically
- Diagnostics appear (either findings or "No issues detected")
- Status bar shows `$(ai-ethics) Scan Complete`
- Output panel (`AI Ethics` tab) shows scan details

### Step 5: (Optional) Set Additional Environment Variables

If you want to enable observability or advanced features, you can also provide:

```bash
# In your terminal (these are read by the MCP backend):
export LANGSMITH_API_KEY="lsv2_..."  # For LangSmith tracing
export TAVILY_API_KEY="tvly_..."     # For web search augmentation

# Then restart VS Code or the extension
```

These keys are only passed to the local Python backend; they are never included in the extension package.

### Step 6: Troubleshooting Connection Issues

If the scan doesn't start or returns errors, check:

**1. Check Python availability:**
```bash
# Verify Python is on your PATH
python --version

# Or test with explicit path (if needed in settings):
/usr/local/bin/python3 --version
```

If missing, set `aiEthics.pythonPath` in settings:
```json
{
  "aiEthics.pythonPath": "/usr/local/bin/python3"
}
```

**2. Check MCP server location:**
```bash
# Verify mcp_server.py exists
ls /Users/aishik/Documents/Programming/ethics_agent/mcp_server.py

# If not in expected path, set it explicitly in settings:
```json
{
  "aiEthics.serverPath": "/Users/aishik/Documents/Programming/ethics_agent/mcp_server.py"
}
```

**3. View extension logs:**
```bash
# Open Command Palette
# Command: "Developer: Show Extension Logs"
# Select "AI Ethics" from the dropdown
# Check for connection or Python errors
```

**4. Restart the extension:**
```bash
# Command Palette: "Developer: Restart Extension Host"
# Or simply reload VS Code (Cmd+R)
```

---

## Part 3: Continuous Updates

When you release a new version:

```bash
# 1. Edit code and tests as needed
# ... make changes to vscode-extension/src/ ...

# 2. Build and verify
cd vscode-extension
npm run compile
cd ..

# 3. Update version in package.json
# Edit vscode-extension/package.json:
# Change "version": "0.1.1" to "0.1.2"

# 4. Update CHANGELOG
# Add entries under "## [Unreleased]" → create new "## [0.1.2] - 2026-04-XX"

# 5. Commit and tag
git add vscode-extension/src vscode-extension/package.json vscode-extension/CHANGELOG.md
git commit -m "Release v0.1.2: [summary]"
git tag vscode-0.1.2
git push origin --tags

# 6. Publish
cd vscode-extension
vsce publish patch  # or explicit version: vsce publish 0.1.2
cd ..

# Users receive auto-update within 24 hours
```
