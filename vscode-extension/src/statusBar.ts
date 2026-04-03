import * as vscode from 'vscode';

export class StatusBarController implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.item.command = 'aiEthics.openProblems';
    this.setIdle();
    this.item.show();
  }

  setIdle(): void {
    this.item.text = '$(shield) AI Ethics: Idle';
    this.item.tooltip = 'Watching for new code edits. The agent runs only after 5 seconds of inactivity.';
  }

  setScheduled(delayMs: number): void {
    const seconds = Math.max(1, Math.round(delayMs / 1000));
    this.item.text = `$(clock) AI Ethics: Check changed code in ${seconds}s…`;
    this.item.tooltip = 'A scan is queued for the latest changed code window.';
  }

  setRunning(): void {
    this.item.text = '$(sync~spin) AI Ethics: Analysing';
    this.item.tooltip = 'Analysing only the most recently changed code region.';
  }

  setClean(): void {
    this.item.text = '$(check) AI Ethics: Changed code clean';
    this.item.tooltip = 'No violations were found in the latest changed code region.';
  }

  setViolations(count: number): void {
    this.item.text = `$(error) AI Ethics: ${count} changed-code violation${count === 1 ? '' : 's'}`;
    this.item.tooltip = 'Violations were found in the latest changed code region.';
  }

  setSkipped(): void {
    this.item.text = '$(shield) AI Ethics: Skipped';
    this.item.tooltip = 'The latest changed code region was skipped.';
  }

  setError(): void {
    this.item.text = '$(warning) AI Ethics: Error';
    this.item.tooltip = 'The latest AI Ethics check failed.';
  }

  dispose(): void {
    this.item.dispose();
  }
}
