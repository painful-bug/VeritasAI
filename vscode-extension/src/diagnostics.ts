import * as vscode from 'vscode';

export interface Finding {
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  file_path: string;
  start_line: number;
  end_line: number;
  regulation_name: string;
  jurisdiction: string;
  explanation: string;
  remedy: string;
  rag_chunk_id: string;
  rag_page: number;
}

export interface FileResult {
  file_path: string;
  file_type: string;
  language: string | null;
  status: 'PASS' | 'WARN' | 'FAIL' | 'ERROR' | 'SKIPPED' | string;
  summary: string;
  predicted_output: string | null;
  findings: Finding[];
  report_path: string | null;
  error: string | null;
  agentic_grade?: {
    relevancy: number;
    faithfulness: number;
    context_quality: number;
    needs_web_search: boolean;
    explanation: string;
    answer: string;
    retrieval_confidence: number;
    trust_level: string;
  } | null;
}

export interface CheckFileResult {
  file_result?: FileResult;
  final_report_md?: string;
  langsmith_run_id?: string | null;
  langsmith_run_url?: string | null;
}

function toSeverity(severity: string): vscode.DiagnosticSeverity {
  if (severity === 'HIGH') {
    return vscode.DiagnosticSeverity.Error;
  }
  if (severity === 'MEDIUM') {
    return vscode.DiagnosticSeverity.Warning;
  }
  return vscode.DiagnosticSeverity.Information;
}

export function findingToDiagnostic(
  finding: Finding,
  document: vscode.TextDocument
): vscode.Diagnostic {
  const lastLine = Math.max(0, document.lineCount - 1);
  const startLine = Math.min(Math.max(0, finding.start_line - 1), lastLine);
  const endLine = Math.min(Math.max(startLine, finding.end_line - 1), lastLine);
  const range = new vscode.Range(
    new vscode.Position(startLine, 0),
    new vscode.Position(endLine, document.lineAt(endLine).text.length)
  );

  const level = finding.severity === 'HIGH'
    ? '[FAILED]'
    : finding.severity === 'MEDIUM'
      ? '[WARN]'
      : '[INFO]';

  const message = [
    `${level} ${finding.regulation_name}`,
    finding.explanation,
    '',
    `Remedy: ${finding.remedy}`,
    `Source: AI Ethics · ${finding.jurisdiction}`
  ].join('\n');

  const diagnostic = new vscode.Diagnostic(range, message, toSeverity(finding.severity));
  diagnostic.source = 'AI Ethics';
  diagnostic.code = finding.regulation_name;
  diagnostic.relatedInformation = [
    new vscode.DiagnosticRelatedInformation(
      new vscode.Location(document.uri, range),
      `Remedy: ${finding.remedy}`
    )
  ];
  return diagnostic;
}
