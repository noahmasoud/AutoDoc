import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import {
  ChangeReportService,
  ChangeReport,
  DiffResult,
  AnalyzerFinding,
} from '../../services/change-report.service';
import { MockChangeReportService } from '../../services/mock-change-report.service';
import { FileDiff } from '../../models/change-report.model';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-run-details',
  standalone: false,
  templateUrl: './run-details.component.html',
  styleUrls: ['./run-details.component.css'],
})
export class RunDetailsComponent implements OnInit, OnDestroy {
  report: ChangeReport | null = null;
  loading = false;
  error: string | null = null;
  searchQuery = '';

  fileDiffs: FileDiff[] = [];
  findingsByFile: { [file: string]: AnalyzerFinding[] } = {};

  filteredFileDiffs: FileDiff[] = [];
  filteredFindings: { [file: string]: AnalyzerFinding[] } = {};

  private routeSubscription?: Subscription;

  useMockData = false;

  constructor(
    private route: ActivatedRoute,
    private changeReportService: ChangeReportService,
    private mockChangeReportService: MockChangeReportService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    this.routeSubscription = this.route.paramMap.subscribe((params) => {
      const runId = params.get('runId');
      if (runId) {
        this.loadReport(runId);
      } else {
        this.error = 'Run ID not provided';
        this.showError('Run ID not found in route parameters');
      }
    });
  }

  ngOnDestroy(): void {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  loadReport(runId: string): void {
    this.loading = true;
    this.error = null;

    // Try to load from backend first
    this.changeReportService.getRunReport(runId).subscribe({
      next: (data) => {
        this.loading = false;
        this.useMockData = false;
        this.report = data;
        this.parseReportData();
        this.applyFilter();
      },
      error: (err: Error) => {
        // Check if it's a network error (backend unavailable)
        const isNetworkError = err.message.includes('Failed to fetch') ||
                              err.message.includes('NetworkError') ||
                              err.message.includes('Http failure') ||
                              err.message.includes('0 Unknown Error');

        if (isNetworkError) {
          // Fallback to mock data for offline development
          console.warn('Backend unavailable, falling back to mock data:', err.message);
          this.loadMockReport(runId);
        } else {
          // Other errors (404, 500, etc.) - show error
          this.loading = false;
          this.error = err.message;
          this.showError(err.message);
        }
      },
    });
  }

  /**
   * Loads mock change report when backend is unavailable.
   *
   * @param runId The run identifier
   */
  private loadMockReport(runId: string): void {
    this.useMockData = true;
    this.mockChangeReportService.getRunReport(runId).subscribe({
      next: (data) => {
        this.loading = false;
        this.report = data;
        this.parseReportData();
        this.applyFilter();
        this.toastService.info('Backend unavailable. Displaying mock data for offline development.');
      },
      error: (err: Error) => {
        this.loading = false;
        this.error = `Failed to load mock data: ${err.message}`;
        this.showError(this.error);
      },
    });
  }

  parseReportData(): void {
    if (!this.report) return;

    // Parse diff summary - ChangeReport uses Record<string, DiffResult>
    const diffSummary = this.report.diff_summary;
    this.fileDiffs = [];

    if (diffSummary && typeof diffSummary === 'object') {
      // File-based diffs (Record<string, DiffResult>)
      this.fileDiffs = Object.entries(diffSummary).map(([fileName, diff]) => ({
        fileName,
        diff: {
          added: diff.added,
          removed: diff.removed,
          modified: diff.modified,
        },
      }));
    }

    // Parse analyzer findings - ChangeReport uses Record<string, AnalyzerFinding[]>
    const findings = this.report.analyzer_findings;
    this.findingsByFile = {};

    if (findings && typeof findings === 'object') {
      // Already grouped by file (Record<string, AnalyzerFinding[]>)
      this.findingsByFile = findings;
    }
  }

  applyFilter(): void {
    if (!this.searchQuery.trim()) {
      this.filteredFileDiffs = this.fileDiffs;
      this.filteredFindings = this.findingsByFile;
      return;
    }

    const query = this.searchQuery.toLowerCase();

    // Filter file diffs
    this.filteredFileDiffs = this.fileDiffs.filter(
      (fileDiff) =>
        fileDiff.fileName.toLowerCase().includes(query) ||
        fileDiff.diff.added?.some((line) => line.toLowerCase().includes(query)) ||
        fileDiff.diff.removed?.some((line) => line.toLowerCase().includes(query)) ||
        fileDiff.diff.modified?.some(
          (mod) =>
            mod.old.toLowerCase().includes(query) || mod.new.toLowerCase().includes(query)
        )
    );

    // Filter findings
    this.filteredFindings = {};
    Object.entries(this.findingsByFile).forEach(([file, findings]) => {
      const matchingFindings = findings.filter(
        (finding) =>
          file.toLowerCase().includes(query) ||
          finding.symbol?.toLowerCase().includes(query) ||
          finding.message?.toLowerCase().includes(query) ||
          finding.type?.toLowerCase().includes(query)
      );

      if (matchingFindings.length > 0) {
        this.filteredFindings[file] = matchingFindings;
      }
    });
  }

  onSearchChange(): void {
    this.applyFilter();
  }

  formatTimestamp(timestamp: string): string {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  }

  showError(message: string): void {
    this.toastService.error(message);
  }

  getSeverityColor(severity?: string): string {
    if (!severity) return '';
    const sev = severity.toLowerCase();
    if (sev === 'error') return 'warn';
    if (sev === 'warning') return 'accent';
    return '';
  }

  /**
   * Helper method to access Object.keys in Angular templates.
   * Required because global objects are not available in strict template checking.
   */
  get objectKeys() {
    return Object.keys;
  }
}

