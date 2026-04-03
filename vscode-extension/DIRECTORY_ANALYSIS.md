<!-- DIRECTORY_ANALYSIS_META {"version": 1, "generated_at": "2026-04-03T19:34:39.306984+00:00", "workspace_root": "/Users/aishik/Documents/Programming/ethics_agent/vscode-extension", "snapshot_hash": "fdf624efbe3712a3e6d7db57c879436eeac11abf65035f3e62404e972494387c", "file_count": 14, "directory_count": 3} -->

# Directory Analysis

Generated: `2026-04-03T19:34:39.306984+00:00`
Workspace root: `/Users/aishik/Documents/Programming/ethics_agent/vscode-extension`
Snapshot hash: `fdf624efbe3712a3e6d7db57c879436eeac11abf65035f3e62404e972494387c`
Files analysed: `14`
Directories analysed: `3`

## Repository Overview

- Purpose: This package is the VS Code frontend for the AI Ethics Compliance Agent. It starts the Python MCP server as a subprocess, sends the active file to `check_file`, and renders streamed findings as native diagnostics. - Repository dependencies installed in the repo root: - `python3 -m venv .venv` - `source .venv/bin/activate` - `pip install -r requirements.txt` - Knowledge base ingested at least once:
- Main themes: this, fields, structural, that, implement, exposes, recognizable, sources
- Dominant languages: JavaScript (4), TypeScript (4), Shell (1)
- File type mix: source_code (9), structured_data (3), document (2)
- Likely entrypoints: None inferred.

## Directory Breakdown

### `.`

- Purpose: Workspace root containing top-level project assets.
- Files: `6`
- Languages: Shell (1)
- Immediate children: `CHANGELOG.md`, `README.md`, `install_extension_locally.sh`, `out`, `package-lock.json`, `package.json`, `src`, `tsconfig.json`

### `out`

- Purpose: out primarily contains source code.
- Files: `4`
- Languages: JavaScript (4)
- Immediate children: `diagnostics.js`, `extension.js`, `mcpClient.js`, `statusBar.js`

### `src`

- Purpose: src primarily contains source code.
- Files: `4`
- Languages: TypeScript (4)
- Immediate children: `diagnostics.ts`, `extension.ts`, `mcpClient.ts`, `statusBar.ts`

## Cross-file Relationships

- `out/extension.js` references `out/diagnostics.js`, `out/mcpClient.js`, `out/statusBar.js`
- `src/extension.ts` references `src/diagnostics.ts`, `src/mcpClient.ts`, `src/statusBar.ts`
- `src/mcpClient.ts` references `src/diagnostics.ts`

## File Breakdown

### `CHANGELOG.md`

- Type: `document`
- Language: `n/a`
- Size: `633` bytes
- Role: CHANGELOG.md is a text document. Sample: # Changelog All notable changes to the AI Ethics Compliance Agent extension will be documented in this file. ## [Unreleased] - Work in progress. ## [0.1.0] -...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: # Changelog All notable changes to the AI Ethics Compliance Agent extension will be documented in this file. ## [Unreleased] - Work in progress. ## [0.1.0] - 2026-04-04 ### Added - Initial release of the AI Ethics Com...
- Preview coverage: Full preview captured within configured limit.

### `README.md`

- Type: `document`
- Language: `n/a`
- Size: `2886` bytes
- Role: README.md is a text document. Sample: # VS Code Extension Runbook This package is the VS Code frontend for the AI Ethics Compliance Agent. It starts the Python MCP server as a subprocess, sends t...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`
- Preview note: # VS Code Extension Runbook This package is the VS Code frontend for the AI Ethics Compliance Agent. It starts the Python MCP server as a subprocess, sends the active file to `check_file`, and renders streamed finding...
- Preview coverage: Full preview captured within configured limit.

### `install_extension_locally.sh`

- Type: `source_code`
- Language: `Shell`
- Size: `139` bytes
- Role: install_extension_locally.sh is Shell code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: #!/bin/bash git add . git commit -m $1 npm run compile && code --install-extension ./vscode-extension/ai-ethics-compliance-agent-0.1.0.vsix
- Preview coverage: Full preview captured within configured limit.

### `package-lock.json`

- Type: `structured_data`
- Language: `n/a`
- Size: `41941` bytes
- Role: package-lock.json appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: `https://registry.npmjs.org/@hono/node-server/-/node-server-1.19.12.tgz`, `https://registry.npmjs.org/@modelcontextprotocol/sdk/-/sdk-1.29.0.tgz`, `https://registry.npmjs.org/@types/node/-/node-20.19.37.tgz`, `https://registry.npmjs.org/@types/vscode/-/vscode-1.110.0.tgz`, `https://registry.npmjs.org/accepts/-/accepts-2.0.0.tgz`, `https://registry.npmjs.org/ajv/-/ajv-8.18.0.tgz`, `https://github.com/sponsors/epoberezkin`, `https://registry.npmjs.org/ajv-formats/-/ajv-formats-3.0.1.tgz`
- Sensitive signals: `age`
- Preview note: { "name": "ai-ethics-compliance-agent", "version": "0.1.0", "lockfileVersion": 3, "requires": true, "packages": { "": { "name": "ai-ethics-compliance-agent", "version": "0.1.0", "dependencies": { "@modelcontextprotoco...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `package.json`

- Type: `structured_data`
- Language: `n/a`
- Size: `2675` bytes
- Role: package.json appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: { "name": "ai-ethics-compliance-agent", "displayName": "AI Ethics Compliance Agent", "description": "Real-time AI ethics compliance diagnostics backed by a Python LangGraph MCP server.", "version": "0.1.0", "publisher...
- Preview coverage: Full preview captured within configured limit.

### `tsconfig.json`

- Type: `structured_data`
- Language: `n/a`
- Size: `377` bytes
- Role: tsconfig.json appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: { "compilerOptions": { "module": "commonjs", "target": "ES2022", "lib": [ "ES2022" ], "outDir": "out", "rootDir": "src", "strict": true, "sourceMap": true, "esModuleInterop": true, "moduleResolution": "node", "types":...
- Preview coverage: Full preview captured within configured limit.

### `out/diagnostics.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `2980` bytes
- Role: diagnostics.js is JavaScript code that appears to implement application logic. It exposes 26 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Remedy, Source, __createBinding, __esModule, __importStar for downstream use.
- Top-level symbols: `vscode`, `toSeverity`, `findingToDiagnostic`, `lastLine`, `startLine`, `endLine`, `range`, `level`, `message`, `diagnostic`
- Schema or fields: `Remedy`, `Source`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `code`, `desc`, `diagnostic`, `endLine`, `enumerable`, `findingToDiagnostic`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `location`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `out/extension.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `21060` bytes
- Role: extension.js is JavaScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as DIRECTORY_ANALYSIS_FILENAME, LangSmith, Report, SUPPORTED_SCAN_EXTENSIONS, Snapshot for downstream use.
- Top-level symbols: `path`, `vscode`, `diagnostics_1`, `mcpClient_1`, `statusBar_1`, `documentStates`, `DIRECTORY_ANALYSIS_FILENAME`, `SUPPORTED_SCAN_EXTENSIONS`, `getConfiguration`, `isEnabled`, `getDebounceMs`, `getWorkspaceTargetPath`
- Schema or fields: `DIRECTORY_ANALYSIS_FILENAME`, `LangSmith`, `Report`, `SUPPORTED_SCAN_EXTENSIONS`, `Snapshot`, `Status`, `Summary`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `absoluteEndLine`
- Internal references: `out/diagnostics.js`, `out/mcpClient.js`, `out/statusBar.js`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `out/mcpClient.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `8635` bytes
- Role: mcpClient.js is JavaScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Checked, ClientCtor, EthicsMcpClient, StdioClientTransportCtor, __createBinding for downstream use.
- Top-level symbols: `path`, `fs`, `vscode`, `requireSdkStdioTransport`, `sdkPackageJson`, `loadMcpClientRuntime`, `clientModule`, `parseProgressMessage`, `parsed`, `extractStructuredContent`, `candidate`, `text`
- Schema or fields: `Checked`, `ClientCtor`, `EthicsMcpClient`, `StdioClientTransportCtor`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `activeDocumentPath`, `args`, `arguments`, `candidate`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `out/statusBar.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `3259` bytes
- Role: statusBar.js is JavaScript code that appears to implement application logic. It exposes 20 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Ethics, StatusBarController, __createBinding, __esModule, __importStar for downstream use.
- Top-level symbols: `vscode`, `StatusBarController`, `seconds`
- Schema or fields: `Ethics`, `StatusBarController`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `command`, `count`, `desc`, `enumerable`, `get`, `item`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `src/diagnostics.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `2473` bytes
- Role: diagnostics.ts is TypeScript code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `toSeverity`, `findingToDiagnostic`, `lastLine`, `startLine`, `endLine`, `range`, `level`, `message`, `diagnostic`
- Schema or fields: `Remedy`, `Source`, `answer`, `code`, `context_quality`, `diagnostic`, `document`, `endLine`, `end_line`, `error`, `explanation`, `faithfulness`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`, `location`
- Preview note: import * as vscode from 'vscode'; export interface Finding { severity: 'HIGH' | 'MEDIUM' | 'LOW' | string; file_path: string; start_line: number; end_line: number; regulation_name: string; jurisdiction: string; explan...
- Preview coverage: Full preview captured within configured limit.

### `src/extension.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `20540` bytes
- Role: extension.ts is TypeScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as ActiveRun, AnalysisSnippet, DIRECTORY_ANALYSIS_FILENAME, DocumentScanState, LangSmith for downstream use.
- Top-level symbols: `documentStates`, `DIRECTORY_ANALYSIS_FILENAME`, `SUPPORTED_SCAN_EXTENSIONS`, `getConfiguration`, `isEnabled`, `getDebounceMs`, `getWorkspaceTargetPath`, `activePath`, `isSupportedFilePath`, `baseName`, `isSupportedDocument`, `documentKey`
- Schema or fields: `ActiveRun`, `AnalysisSnippet`, `DIRECTORY_ANALYSIS_FILENAME`, `DocumentScanState`, `LangSmith`, `PendingChangeWindow`, `Report`, `SUPPORTED_SCAN_EXTENSIONS`, `Snapshot`, `Status`, `Summary`, `absoluteEndLine`
- Internal references: `src/diagnostics.ts`, `src/mcpClient.ts`, `src/statusBar.ts`
- Data sources: None detected.
- Sensitive signals: `ssn`
- Preview note: import * as path from 'path'; import * as vscode from 'vscode'; import { CheckFileResult, FileResult, Finding, findingToDiagnostic } from './diagnostics'; import { DirectoryAnalysisResult, EthicsMcpClient } from './mc...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `src/mcpClient.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `8763` bytes
- Role: mcpClient.ts is TypeScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Checked, ClientCtor, DirectoryAnalysisResult, McpClientLike, ProgressPayload for downstream use.
- Top-level symbols: `requireSdkStdioTransport`, `sdkPackageJson`, `loadMcpClientRuntime`, `clientModule`, `parseProgressMessage`, `parsed`, `extractStructuredContent`, `candidate`, `text`, `candidateSearchRoots`, `roots`, `activeDocumentPath`
- Schema or fields: `Checked`, `ClientCtor`, `DirectoryAnalysisResult`, `McpClientLike`, `ProgressPayload`, `ReviewedContextItem`, `StdioClientTransportCtor`, `StdioTransportLike`, `activeDocumentPath`, `analysis_path`, `args`, `arguments`
- Internal references: `src/diagnostics.ts`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: import * as path from 'path'; import * as fs from 'fs'; import * as vscode from 'vscode'; import type { CheckFileResult } from './diagnostics'; type ProgressPayload = { type: string; data?: unknown; }; export type Dir...
- Preview coverage: Full preview captured within configured limit.

### `src/statusBar.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `1714` bytes
- Role: statusBar.ts is TypeScript code that appears to implement application logic. It exposes 8 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Ethics, command, count, delayMs, item for downstream use.
- Top-level symbols: `StatusBarController`, `seconds`
- Schema or fields: `Ethics`, `command`, `count`, `delayMs`, `item`, `seconds`, `text`, `tooltip`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: import * as vscode from 'vscode'; export class StatusBarController implements vscode.Disposable { private readonly item: vscode.StatusBarItem; constructor() { this.item = vscode.window.createStatusBarItem(vscode.Statu...
- Preview coverage: Full preview captured within configured limit.
