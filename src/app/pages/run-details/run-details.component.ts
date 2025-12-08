import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
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
import { PatchesService, Patch } from '../../services/patches.service';

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

  patches: Patch[] = [];
  loadingPatches = false;

  private routeSubscription?: Subscription;

  useMockData = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private changeReportService: ChangeReportService,
    private mockChangeReportService: MockChangeReportService,
    private toastService: ToastService,
    private patchesService: PatchesService
  ) {}

  ngOnInit(): void {
    this.routeSubscription = this.route.paramMap.subscribe((params) => {
      const runId = params.get('runId');
      if (runId) {
        this.loadReport(runId);
        this.loadPatches(parseInt(runId, 10));
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
      error: (err: any) => {
        // Check if it's a network error (backend unavailable)
        const errorMessage = err?.error?.detail || err?.message || 'Unknown error';
        
        // HTTP errors from the service include status codes in the message like ": 404 Not Found"
        // Network errors don't have status codes in the message
        const hasHttpStatusInMessage = /:\s*\d{3}\s+/.test(errorMessage);
        const hasHttpStatus = err?.status !== undefined && err?.status !== 0 && err?.status !== null;
        
        // Only treat as network error if it's a true network failure
        // (no HTTP status code in error object AND no status code in message)
        const isNetworkError = !hasHttpStatus && !hasHttpStatusInMessage &&
                              (errorMessage.includes('NetworkError') ||
                               errorMessage.includes('0 Unknown Error') ||
                               (errorMessage.includes('Failed to fetch') && !hasHttpStatusInMessage));

        if (isNetworkError) {
          // Fallback to mock data for offline development
          console.warn('Backend unavailable, falling back to mock data:', errorMessage);
          this.loadMockReport(runId);
        } else {
          // Other errors (404, 500, etc.) - show error
          this.loading = false;
          this.error = errorMessage;
          this.showError(errorMessage);
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

  loadPatches(runId: number): void {
    this.loadingPatches = true;
    this.patchesService.listPatches(runId).subscribe({
      next: (patches) => {
        this.patches = patches;
        this.loadingPatches = false;
      },
      error: (err) => {
        this.loadingPatches = false;
        console.warn('Failed to load patches:', err);
        // Don't show error toast for patches - it's optional data
      },
    });
  }

  viewPatch(patchId: number): void {
    const runId = this.route.snapshot.paramMap.get('runId');
    this.router.navigate(['/runs', runId, 'patches', patchId]);
  }

  getStatusColor(status: string): string {
    switch (status?.toLowerCase()) {
      case 'applied':
        return 'primary';
      case 'error':
        return 'warn';
      case 'awaiting review':
        return 'accent';
      default:
        return '';
    }
  }
}

