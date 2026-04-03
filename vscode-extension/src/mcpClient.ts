import * as path from 'path';
import * as fs from 'fs';
import * as vscode from 'vscode';

import type { CheckFileResult } from './diagnostics';

type ProgressPayload = {
  type: string;
  data?: unknown;
};

export type DirectoryAnalysisResult = {
  workspace_root?: string;
  analysis_path: string;
  content?: string;
  updated: boolean;
  snapshot_hash?: string;
  file_count: number;
  directory_count: number;
};

type McpClientLike = {
  connect: (transport: unknown) => Promise<void>;
  close?: () => Promise<void>;
  callTool: (
    request: { name: string; arguments: Record<string, unknown> },
    resultSchema: unknown | undefined,
    options?: {
      onprogress?: (event: { progress: number; total?: number; message?: string }) => void;
      timeout?: number;
      resetTimeoutOnProgress?: boolean;
      maxTotalTimeout?: number;
    }
  ) => Promise<unknown>;
};

type ReviewedContextItem = {
  start_line: number;
  end_line: number;
  summary: string;
  findings: Array<{
    severity: string;
    file_path: string;
    start_line: number;
    end_line: number;
    regulation_name: string;
    jurisdiction: string;
    explanation: string;
    remedy: string;
    rag_chunk_id: string;
    rag_page: number;
  }>;
};

type StdioTransportLike = {
  stderr?: NodeJS.ReadableStream | null;
};

function requireSdkStdioTransport(): unknown {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const sdkPackageJson = require.resolve('@modelcontextprotocol/sdk/package.json');
  try {
    // This path is exported by some SDK versions, but broken in others.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require('@modelcontextprotocol/sdk/client/stdio').StdioClientTransport;
  } catch {
    // Fallback to the actual compiled file inside the installed SDK package.
    return require(path.join(path.dirname(sdkPackageJson), 'client', 'stdio.js')).StdioClientTransport;
  }
}

function loadMcpClientRuntime(): { ClientCtor: new (...args: any[]) => McpClientLike; StdioClientTransportCtor: new (...args: any[]) => unknown } {
  // Always use the SDK bundled with this extension to avoid runtime mismatches.
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const clientModule = require('@modelcontextprotocol/sdk/client');
  return {
    ClientCtor: clientModule.Client ?? clientModule.MCPClient,
    StdioClientTransportCtor: requireSdkStdioTransport() as new (...args: any[]) => unknown
  };
}

function parseProgressMessage(message: string | undefined): ProgressPayload | null {
  if (!message) {
    return null;
  }
  try {
    const parsed = JSON.parse(message) as ProgressPayload;
    return typeof parsed?.type === 'string' ? parsed : null;
  } catch {
    return null;
  }
}

function extractStructuredContent<T>(result: unknown): T {
  const candidate = result as {
    structuredContent?: T;
    content?: Array<{ text?: string }>;
  };

  if (candidate?.structuredContent && typeof candidate.structuredContent === 'object') {
    return candidate.structuredContent;
  }

  const text = candidate?.content?.find(item => typeof item.text === 'string')?.text;
  if (!text) {
    return {} as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    return {} as T;
  }
}

function candidateSearchRoots(): string[] {
  const roots = new Set<string>();

  for (const folder of vscode.workspace.workspaceFolders ?? []) {
    roots.add(folder.uri.fsPath);
  }

  const activeDocumentPath = vscode.window.activeTextEditor?.document.uri.fsPath;
  if (activeDocumentPath) {
    roots.add(path.dirname(activeDocumentPath));
  }

  return Array.from(roots);
}

function ancestorCandidates(startPath: string): string[] {
  const candidates: string[] = [];
  let current = path.resolve(startPath);

  while (true) {
    candidates.push(path.join(current, 'mcp_server.py'));
    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }

  return candidates;
}

function resolveServerPath(configuration: vscode.WorkspaceConfiguration): string {
  const explicit = configuration.get<string>('serverPath', '').trim();
  if (explicit) {
    if (!fs.existsSync(explicit)) {
      throw new Error(`Configured aiEthics.serverPath does not exist: ${explicit}`);
    }
    return explicit;
  }

  const searchRoots = candidateSearchRoots();
  if (searchRoots.length === 0) {
    throw new Error('No workspace folder is open and aiEthics.serverPath is not configured.');
  }

  const seen = new Set<string>();
  const candidates: string[] = [];

  for (const root of searchRoots) {
    for (const candidate of ancestorCandidates(root)) {
      if (!seen.has(candidate)) {
        seen.add(candidate);
        candidates.push(candidate);
      }
    }
  }

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return path.resolve(candidate);
    }
  }

  throw new Error(
    `Could not find mcp_server.py. Checked: ${candidates.map(candidate => path.resolve(candidate)).join(', ')}`
  );
}

export class EthicsMcpClient implements vscode.Disposable {
  private client: McpClientLike | undefined;
  private transport: unknown;

  constructor(private readonly output: vscode.OutputChannel) {}

  private async getClient(): Promise<McpClientLike> {
    if (this.client) {
      return this.client;
    }

    const configuration = vscode.workspace.getConfiguration('aiEthics');
    const pythonPath = configuration.get<string>('pythonPath', 'python');
    const serverPath = resolveServerPath(configuration);
    const serverCwd = path.dirname(serverPath);
    const { ClientCtor, StdioClientTransportCtor } = loadMcpClientRuntime();

    this.transport = new StdioClientTransportCtor({
      command: pythonPath,
      args: [serverPath],
      cwd: serverCwd,
      env: process.env,
      stderr: 'pipe'
    });
    this.client = new ClientCtor({ name: 'ai-ethics-vscode', version: '0.1.0' });
    const stderrStream = (this.transport as StdioTransportLike).stderr;
    if (stderrStream && typeof stderrStream.on === 'function') {
      stderrStream.on('data', chunk => {
        this.output.appendLine(`[mcp stderr] ${String(chunk).trimEnd()}`);
      });
    }
    this.output.appendLine(`Connecting MCP client: ${pythonPath} ${serverPath} (cwd=${serverCwd})`);
    await this.client.connect(this.transport);
    return this.client;
  }

  async checkFile(
    request: {
      filePath: string;
      fileContent: string;
      lineOffset?: number;
      reviewedContext?: ReviewedContextItem[];
      provider: string;
      model: string;
    },
    onEvent: (payload: ProgressPayload) => void
  ): Promise<CheckFileResult> {
    const client = await this.getClient();
    const timeoutMs = vscode.workspace.getConfiguration('aiEthics').get<number>('requestTimeoutMs', 300_000);
    const response = await client.callTool(
      {
        name: 'check_file',
        arguments: {
          file_path: request.filePath,
          file_content: request.fileContent,
          line_offset: request.lineOffset ?? 0,
          reviewed_context: request.reviewedContext ?? [],
          provider: request.provider,
          model: request.model
        }
      },
      undefined,
      {
        timeout: timeoutMs,
        onprogress: event => {
          const payload = parseProgressMessage(event.message);
          if (payload) {
            onEvent(payload);
          }
        },
        resetTimeoutOnProgress: true,
        maxTotalTimeout: timeoutMs
      }
    );

    return extractStructuredContent<CheckFileResult>(response);
  }

  async refreshDirectoryAnalysis(
    request: {
      targetDirectory: string;
      force?: boolean;
    },
    onEvent?: (payload: ProgressPayload) => void
  ): Promise<DirectoryAnalysisResult> {
    const client = await this.getClient();
    const timeoutMs = vscode.workspace.getConfiguration('aiEthics').get<number>('requestTimeoutMs', 300_000);
    const response = await client.callTool(
      {
        name: 'refresh_directory_analysis',
        arguments: {
          target_directory: request.targetDirectory,
          force: request.force ?? true
        }
      },
      undefined,
      {
        timeout: timeoutMs,
        onprogress: event => {
          const payload = parseProgressMessage(event.message);
          if (payload && onEvent) {
            onEvent(payload);
          }
        },
        resetTimeoutOnProgress: true,
        maxTotalTimeout: timeoutMs
      }
    );

    return extractStructuredContent<DirectoryAnalysisResult>(response);
  }

  async dispose(): Promise<void> {
    if (this.client?.close) {
      await this.client.close();
    }
    this.client = undefined;
    this.transport = undefined;
  }
}
