/** TypeScript interfaces for change report API responses. */

export interface ModifiedLine {
  line: number;
  old: string;
  new: string;
}

export interface DiffSummary {
  added?: string[];
  removed?: string[];
  modified?: ModifiedLine[];
}

export interface AnalyzerFinding {
  file?: string;
  symbol?: string;
  type?: string;
  severity?: string;
  message?: string;
  [key: string]: unknown;
}

export interface AnalyzerFindings {
  [file: string]: AnalyzerFinding[];
}

export interface ChangeReport {
  run_id: string;
  timestamp: string;
  diff_summary: DiffSummary | { [file: string]: DiffSummary };
  analyzer_findings: AnalyzerFindings | AnalyzerFinding[];
}

export interface FileDiff {
  fileName: string;
  diff: DiffSummary;
}

