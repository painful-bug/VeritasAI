import * as path from 'path';
import * as vscode from 'vscode';

import { CheckFileResult, FileResult, Finding, findingToDiagnostic } from './diagnostics';
import { DirectoryAnalysisResult, EthicsMcpClient } from './mcpClient';
import { StatusBarController } from './statusBar';

type PendingChangeWindow = {
  startLine: number;
  endLine: number;
  lastChangeAt: number;
  lineDelta: number;
};

type AnalysisSnippet = {
  text: string;
  absoluteStartLine: number;
  absoluteEndLine: number;
  changedStartLine: number;
  changedEndLine: number;
};

type DocumentScanState = {
  pendingWindow?: PendingChangeWindow;
  timer?: NodeJS.Timeout;
  findings: Finding[];
};

type ActiveRun = {
  documentUri: string;
  documentVersion: number;
  snippet: AnalysisSnippet;
  pendingWindow: PendingChangeWindow;
};

let diagnosticCollection: vscode.DiagnosticCollection;
let statusBar: StatusBarController;
let outputChannel: vscode.OutputChannel;
let mcpClient: EthicsMcpClient;
let activeRun: ActiveRun | undefined;

const documentStates = new Map<string, DocumentScanState>();
const DIRECTORY_ANALYSIS_FILENAME = 'directory_analysis.md';
const SUPPORTED_SCAN_EXTENSIONS = new Set([
  '.py',
  '.js',
  '.jsx',
  '.ts',
  '.tsx',
  '.java',
  '.go',
  '.rs',
  '.c',
  '.cpp',
  '.cs',
  '.rb',
  '.php',
  '.swift',
  '.kt',
  '.sh',
  '.md',
  '.txt',
  '.rst',
  '.pdf',
  '.docx',
  '.doc',
  '.html',
  '.htm',
  '.csv',
  '.tsv',
  '.json',
  '.jsonl',
  '.yaml',
  '.yml',
  '.xml'
]);

function getConfiguration(): vscode.WorkspaceConfiguration {
  return vscode.workspace.getConfiguration('aiEthics');
}

function isEnabled(): boolean {
  return getConfiguration().get<boolean>('enabled', true);
}

function getDebounceMs(): number {
  return getConfiguration().get<number>('debounceMs', 5000);
}

function getWorkspaceTargetPath(): string | undefined {
  const activePath = vscode.window.activeTextEditor?.document.uri.fsPath;
  if (activePath) {
    return activePath;
  }
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function isSupportedFilePath(filePath: string): boolean {
  const baseName = path.basename(filePath).toLowerCase();
  if (baseName === DIRECTORY_ANALYSIS_FILENAME) {
    return false;
  }
  return SUPPORTED_SCAN_EXTENSIONS.has(path.extname(filePath).toLowerCase());
}

function isSupportedDocument(document: vscode.TextDocument): boolean {
  return document.uri.scheme === 'file' && !document.isClosed && isSupportedFilePath(document.fileName);
}

function documentKey(documentOrUri: vscode.TextDocument | vscode.Uri): string {
  return documentOrUri instanceof vscode.Uri ? documentOrUri.toString() : documentOrUri.uri.toString();
}

function getDocumentState(documentOrUri: vscode.TextDocument | vscode.Uri): DocumentScanState {
  const key = documentKey(documentOrUri);
  const existing = documentStates.get(key);
  if (existing) {
    return existing;
  }

  const created: DocumentScanState = { findings: [] };
  documentStates.set(key, created);
  return created;
}

function clearTimer(state: DocumentScanState): void {
  if (state.timer) {
    clearTimeout(state.timer);
    state.timer = undefined;
  }
}

function disposeDocumentState(documentOrUri: vscode.TextDocument | vscode.Uri): void {
  const key = documentKey(documentOrUri);
  const state = documentStates.get(key);
  if (!state) {
    return;
  }

  clearTimer(state);
  documentStates.delete(key);
}

function hasMeaningfulChange(event: vscode.TextDocumentChangeEvent): boolean {
  return event.contentChanges.some(change => change.text.length > 0 || !change.range.isEmpty);
}

function mergeWindows(current: PendingChangeWindow | undefined, next: PendingChangeWindow): PendingChangeWindow {
  if (!current) {
    return next;
  }

  return {
    startLine: Math.min(current.startLine, next.startLine),
    endLine: Math.max(current.endLine, next.endLine),
    lastChangeAt: Math.max(current.lastChangeAt, next.lastChangeAt),
    lineDelta: current.lineDelta + next.lineDelta
  };
}

function toPendingWindow(event: vscode.TextDocumentChangeEvent): PendingChangeWindow | undefined {
  if (!hasMeaningfulChange(event)) {
    return undefined;
  }

  let startLine = Number.MAX_SAFE_INTEGER;
  let endLine = 1;
  let lineDelta = 0;

  for (const change of event.contentChanges) {
    const insertedLines = change.text.length === 0 ? 0 : change.text.split(/\r?\n/).length - 1;
    const deletedLines = Math.max(0, change.range.end.line - change.range.start.line);
    const candidateStart = change.range.start.line + 1;
    const candidateEnd = Math.max(change.range.end.line + 1, candidateStart + insertedLines);
    startLine = Math.min(startLine, candidateStart);
    endLine = Math.max(endLine, candidateEnd);
    lineDelta += insertedLines - deletedLines;
  }

  if (!Number.isFinite(startLine)) {
    return undefined;
  }

  return {
    startLine,
    endLine,
    lastChangeAt: Date.now(),
    lineDelta
  };
}

function buildSnippet(document: vscode.TextDocument, pendingWindow: PendingChangeWindow): AnalysisSnippet {
  const lastLine = Math.max(1, document.lineCount);
  const startLine = Math.min(Math.max(1, pendingWindow.startLine), lastLine);
  const endLine = Math.min(Math.max(startLine, pendingWindow.endLine), lastLine);
  const range = new vscode.Range(
    new vscode.Position(startLine - 1, 0),
    new vscode.Position(endLine - 1, document.lineAt(endLine - 1).text.length)
  );

  return {
    text: document.getText(range),
    absoluteStartLine: startLine,
    absoluteEndLine: endLine,
    changedStartLine: pendingWindow.startLine,
    changedEndLine: pendingWindow.endLine
  };
}

function setDiagnostics(document: vscode.TextDocument, findings: Finding[]): void {
  const diagnostics = findings.map(finding => findingToDiagnostic(finding, document));
  diagnosticCollection.set(document.uri, diagnostics);
}

function shiftFindingLines(finding: Finding, lineDelta: number): Finding {
  return {
    ...finding,
    start_line: Math.max(1, finding.start_line + lineDelta),
    end_line: Math.max(1, finding.end_line + lineDelta)
  };
}

function overlapsWindow(window: PendingChangeWindow, finding: Finding): boolean {
  return finding.end_line >= window.startLine && finding.start_line <= window.endLine;
}

function normalizeFindingsAfterChange(state: DocumentScanState, window: PendingChangeWindow): void {
  const updated: Finding[] = [];
  for (const finding of state.findings) {
    if (overlapsWindow(window, finding)) {
      continue;
    }
    if (finding.start_line > window.endLine) {
      updated.push(shiftFindingLines(finding, window.lineDelta));
      continue;
    }
    updated.push(finding);
  }
  state.findings = updated;
}

function buildReviewedContext(
  state: DocumentScanState,
  window: PendingChangeWindow
): Array<{ start_line: number; end_line: number; summary: string; findings: Finding[] }> {
  const nearby = state.findings.filter(finding => {
    return finding.start_line <= window.endLine + 40 && finding.end_line >= Math.max(1, window.startLine - 40);
  });

  if (nearby.length === 0) {
    return [];
  }

  return [
    {
      start_line: Math.min(...nearby.map(finding => finding.start_line)),
      end_line: Math.max(...nearby.map(finding => finding.end_line)),
      summary: `Previously reviewed code near lines ${window.startLine}-${window.endLine}.`,
      findings: nearby.slice(0, 8)
    }
  ];
}

function updateStatusFromResult(result: FileResult | undefined): void {
  if (!result) {
    statusBar.setError();
    return;
  }

  if (result.status === 'SKIPPED') {
    statusBar.setSkipped();
    return;
  }

  if (result.status === 'ERROR') {
    statusBar.setError();
    return;
  }

  if ((result.findings ?? []).length > 0) {
    statusBar.setViolations(result.findings.length);
    return;
  }

  statusBar.setClean();
}

function appendResultOutput(result: CheckFileResult): void {
  const fileResult = result.file_result;
  if (fileResult) {
    outputChannel.appendLine(`Status: ${fileResult.status}`);
    outputChannel.appendLine(`Summary: ${fileResult.summary}`);
    if (fileResult.agentic_grade) {
      const grade = fileResult.agentic_grade;
      outputChannel.appendLine(
        `Self-grade: rel=${grade.relevancy.toFixed(2)} faith=${grade.faithfulness.toFixed(2)} ctx=${grade.context_quality.toFixed(2)} trust=${grade.trust_level}`
      );
      outputChannel.appendLine(`Needs web search: ${grade.needs_web_search}`);
    }
    if (fileResult.report_path) {
      outputChannel.appendLine(`Report: ${fileResult.report_path}`);
    }
  }
  if (result.langsmith_run_url) {
    outputChannel.appendLine(`LangSmith: ${result.langsmith_run_url}`);
  }
  outputChannel.appendLine('');
}

function appendDirectoryAnalysisOutput(result: DirectoryAnalysisResult): void {
  outputChannel.appendLine(`Directory analysis: ${result.updated ? 'updated' : 'loaded'} ${result.analysis_path}`);
  outputChannel.appendLine(`Files analysed: ${result.file_count}`);
  outputChannel.appendLine(`Directories analysed: ${result.directory_count}`);
  if (result.snapshot_hash) {
    outputChannel.appendLine(`Snapshot: ${result.snapshot_hash}`);
  }
  outputChannel.appendLine('');
}

async function runDirectoryAnalysis(force: boolean): Promise<void> {
  const targetPath = getWorkspaceTargetPath();
  if (!targetPath) {
    void vscode.window.showErrorMessage('AI Ethics could not determine a workspace path for directory analysis.');
    return;
  }

  statusBar.setRunning();
  outputChannel.appendLine(`${force ? 'Refreshing' : 'Creating'} directory analysis for ${targetPath}`);

  try {
    const result = await mcpClient.refreshDirectoryAnalysis(
      { targetDirectory: targetPath, force },
      event => {
        if (event.type === 'directory_analysis_started' || event.type === 'directory_analysis_ready') {
          statusBar.setRunning();
        }
      }
    );
    appendDirectoryAnalysisOutput(result);
    statusBar.setIdle();

    if (result.analysis_path) {
      const document = await vscode.workspace.openTextDocument(result.analysis_path);
      await vscode.window.showTextDocument(document, { preview: false });
    }

    void vscode.window.showInformationMessage(
      `AI Ethics directory analysis ${result.updated ? 'updated' : 'loaded'}: ${result.analysis_path}`
    );
  } catch (error) {
    statusBar.setError();
    const message = error instanceof Error ? error.message : String(error);
    outputChannel.appendLine(`Directory analysis failed: ${message}`);
    outputChannel.appendLine('');
    void vscode.window.showErrorMessage(`AI Ethics directory analysis failed: ${message}`);
  }
}

async function ensureDirectoryAnalysisOnStartup(): Promise<void> {
  const targetPath = getWorkspaceTargetPath();
  if (!targetPath) {
    return;
  }

  try {
    const result = await mcpClient.refreshDirectoryAnalysis({ targetDirectory: targetPath, force: false });
    if (result.updated) {
      outputChannel.appendLine(`Created repository directory analysis at ${result.analysis_path}`);
      outputChannel.appendLine('');
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    outputChannel.appendLine(`Automatic directory analysis bootstrap failed: ${message}`);
    outputChannel.appendLine('');
  }
}

function scheduleCheck(document: vscode.TextDocument): void {
  if (!isEnabled() || !isSupportedDocument(document)) {
    return;
  }

  const state = getDocumentState(document);
  clearTimer(state);

  const debounceMs = getDebounceMs();
  state.timer = setTimeout(() => {
    state.timer = undefined;
    void startReadyChecks();
  }, debounceMs);

  statusBar.setScheduled(debounceMs);
}

function findOpenDocument(uri: string): vscode.TextDocument | undefined {
  return vscode.workspace.textDocuments.find(document => document.uri.toString() === uri);
}

function pickReadyDocument(): { document: vscode.TextDocument; state: DocumentScanState; pendingWindow: PendingChangeWindow } | undefined {
  const now = Date.now();
  const debounceMs = getDebounceMs();
  const activeEditorUri = vscode.window.activeTextEditor?.document.uri.toString();
  const candidates: Array<{ document: vscode.TextDocument; state: DocumentScanState; pendingWindow: PendingChangeWindow; priority: number }> = [];

  for (const document of vscode.workspace.textDocuments) {
    if (!isSupportedDocument(document)) {
      continue;
    }

    const state = documentStates.get(document.uri.toString());
    if (!state?.pendingWindow) {
      continue;
    }

    if (now - state.pendingWindow.lastChangeAt < debounceMs) {
      continue;
    }

    candidates.push({
      document,
      state,
      pendingWindow: state.pendingWindow,
      priority: document.uri.toString() === activeEditorUri ? 0 : 1
    });
  }

  candidates.sort((left, right) => {
    if (left.priority !== right.priority) {
      return left.priority - right.priority;
    }
    return left.pendingWindow.lastChangeAt - right.pendingWindow.lastChangeAt;
  });

  return candidates[0];
}

async function runComplianceCheck(document: vscode.TextDocument, pendingWindow: PendingChangeWindow): Promise<void> {
  if (!isEnabled() || !isSupportedDocument(document)) {
    return;
  }

  const configuration = getConfiguration();
  const provider = configuration.get<string>('provider', 'ollama_cloud');
  const model = configuration.get<string>('model', 'glm4:cloud');
  const state = getDocumentState(document);
  const findings: Finding[] = [];
  const snippet = buildSnippet(document, pendingWindow);
  const documentUri = document.uri.toString();
  const reviewedContext = buildReviewedContext(state, pendingWindow);

  if (!snippet.text.trim()) {
    return;
  }

  activeRun = {
    documentUri,
    documentVersion: document.version,
    snippet,
    pendingWindow
  };

  diagnosticCollection.delete(document.uri);
  statusBar.setRunning();
  outputChannel.appendLine(
    `Checking ${document.fileName} changed lines ${snippet.changedStartLine}-${snippet.changedEndLine}`
  );

  try {
    const result = await mcpClient.checkFile(
      {
        filePath: document.fileName,
        fileContent: snippet.text,
        lineOffset: snippet.absoluteStartLine - 1,
        reviewedContext,
        provider,
        model
      },
      event => {
        if (!activeRun || activeRun.documentUri !== documentUri) {
          return;
        }

        if (event.type === 'violation_found' && event.data) {
          findings.push(event.data as Finding);
          setDiagnostics(document, findings);
          statusBar.setViolations(findings.length);
          return;
        }

        if (event.type === 'scan_progress') {
          statusBar.setRunning();
        }
      }
    );

    const currentState = getDocumentState(document);
    if (currentState.pendingWindow) {
      outputChannel.appendLine(`Discarded stale result for ${document.fileName} because newer code arrived.`);
      outputChannel.appendLine('');
      return;
    }

    const latestDocument = findOpenDocument(documentUri);
    if (!latestDocument || latestDocument.version !== activeRun.documentVersion) {
      outputChannel.appendLine(`Discarded stale result for ${document.fileName} because the document changed.`);
      outputChannel.appendLine('');
      statusBar.setIdle();
      return;
    }

    const finalResult = result.file_result;
    if (finalResult?.findings && finalResult.findings.length > findings.length) {
      state.findings = [
        ...state.findings.filter(finding => !overlapsWindow(pendingWindow, finding)),
        ...finalResult.findings
      ];
      setDiagnostics(latestDocument, state.findings);
    } else if (findings.length > 0) {
      state.findings = [
        ...state.findings.filter(finding => !overlapsWindow(pendingWindow, finding)),
        ...findings
      ];
      setDiagnostics(latestDocument, state.findings);
    }

    updateStatusFromResult(finalResult);
    appendResultOutput(result);
  } catch (error) {
    const currentState = getDocumentState(document);
    if (currentState.pendingWindow) {
      return;
    }

    statusBar.setError();
    diagnosticCollection.delete(document.uri);
    const message = error instanceof Error ? error.message : String(error);
    outputChannel.appendLine(`Check failed: ${message}`);
    void vscode.window.showErrorMessage(`AI Ethics check failed: ${message}`);
  } finally {
    activeRun = undefined;
    void startReadyChecks();
  }
}

async function startReadyChecks(): Promise<void> {
  if (activeRun || !isEnabled()) {
    return;
  }

  const ready = pickReadyDocument();
  if (!ready) {
    return;
  }

  ready.state.pendingWindow = undefined;
  await runComplianceCheck(ready.document, ready.pendingWindow);
}

function handleDocumentChange(event: vscode.TextDocumentChangeEvent): void {
  if (!isEnabled() || !isSupportedDocument(event.document) || event.contentChanges.length === 0) {
    return;
  }

  const pendingWindow = toPendingWindow(event);
  if (!pendingWindow) {
    return;
  }

  const state = getDocumentState(event.document);
  normalizeFindingsAfterChange(state, pendingWindow);
  state.pendingWindow = mergeWindows(state.pendingWindow, pendingWindow);
  setDiagnostics(event.document, state.findings);
  scheduleCheck(event.document);
}

function clearAllScheduledChecks(): void {
  for (const state of documentStates.values()) {
    clearTimer(state);
    state.pendingWindow = undefined;
    state.findings = [];
  }
}

export function activate(context: vscode.ExtensionContext): void {
  diagnosticCollection = vscode.languages.createDiagnosticCollection('ai-ethics');
  statusBar = new StatusBarController();
  outputChannel = vscode.window.createOutputChannel('AI Ethics');
  mcpClient = new EthicsMcpClient(outputChannel);

  context.subscriptions.push(
    diagnosticCollection,
    statusBar,
    outputChannel,
    new vscode.Disposable(() => {
      clearAllScheduledChecks();
      void mcpClient.dispose();
    }),
    vscode.commands.registerCommand('aiEthics.openProblems', async () => {
      await vscode.commands.executeCommand('workbench.actions.view.problems');
    }),
    vscode.commands.registerCommand('aiEthics.showOutput', () => {
      outputChannel.show(true);
    }),
    vscode.commands.registerCommand('aiEthics.createDirectoryAnalysis', async () => {
      await runDirectoryAnalysis(false);
    }),
    vscode.commands.registerCommand('aiEthics.refreshDirectoryAnalysis', async () => {
      await runDirectoryAnalysis(true);
    }),
    vscode.workspace.onDidChangeTextDocument(handleDocumentChange),
    vscode.workspace.onDidCloseTextDocument(document => {
      diagnosticCollection.delete(document.uri);
      disposeDocumentState(document);
    }),
    vscode.workspace.onDidChangeConfiguration(event => {
      if (!event.affectsConfiguration('aiEthics')) {
        return;
      }

      if (!isEnabled()) {
        clearAllScheduledChecks();
        diagnosticCollection.clear();
        statusBar.setIdle();
      }
    })
  );

  void ensureDirectoryAnalysisOnStartup();
}

export function deactivate(): void {
  clearAllScheduledChecks();
  void mcpClient?.dispose();
}
