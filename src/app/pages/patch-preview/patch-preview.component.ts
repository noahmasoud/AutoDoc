import { Component, OnInit, OnDestroy, HostListener, ViewChild, ElementRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { PatchesService, Patch, StructuredDiff, ModifiedLine } from '../../services/patches.service';
import { ToastService } from '../../services/toast.service';
import { AuthService } from '../../services/auth.service';

interface DiffLine {
  type: 'unchanged' | 'added' | 'removed' | 'modified';
  beforeLine?: string;
  afterLine?: string;
  lineNumber?: number;
}

@Component({
  selector: 'app-patch-preview',
  standalone: false,
  templateUrl: './patch-preview.component.html',
  styleUrls: ['./patch-preview.component.css'],
})
export class PatchPreviewComponent implements OnInit, OnDestroy {
  patch: Patch | null = null;
  loading = false;
  error: string | null = null;
  runId: string | null = null;
  patchId: string | null = null;
  
  // Side-by-side diff data
  diffLines: DiffLine[] = [];
  beforeLines: string[] = [];
  afterLines: string[] = [];
  
  // Approve/Reject state
  approving = false;
  rejecting = false;
  rejectComment = '';
  showRejectDialog = false;
  
  // Focus management
  @ViewChild('approveButton', { static: false }) approveButton?: ElementRef<HTMLButtonElement>;
  @ViewChild('rejectButton', { static: false }) rejectButton?: ElementRef<HTMLButtonElement>;
  @ViewChild('commentInput', { static: false }) commentInput?: ElementRef<HTMLTextAreaElement>;
  
  private routeSubscription?: Subscription;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private patchesService: PatchesService,
    private toastService: ToastService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.routeSubscription = this.route.paramMap.subscribe((params) => {
      this.runId = params.get('runId');
      this.patchId = params.get('patchId');
      if (this.patchId) {
        this.loadPatch(parseInt(this.patchId, 10));
      } else {
        this.error = 'Patch ID not provided';
        this.showError('Patch ID not found in route parameters');
      }
    });
  }

  ngOnDestroy(): void {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  loadPatch(patchId: number): void {
    this.loading = true;
    this.error = null;

    this.patchesService.getPatch(patchId).subscribe({
      next: (patch) => {
        this.patch = patch;
        this.processDiff();
        this.loading = false;
      },
      error: (err: any) => {
        this.loading = false;
        this.error = err.error?.detail || err.message || 'Failed to load patch';
        if (this.error) {
          this.showError(this.error);
        }
      },
    });
  }

  processDiff(): void {
    if (!this.patch) return;

    // Use structured diff if available, otherwise fall back to before/after comparison
    if (this.patch.diff_structured) {
      this.processStructuredDiff(this.patch.diff_structured);
    } else {
      // Fallback: split before/after into lines and create a simple diff
      this.beforeLines = this.patch.diff_before.split('\n');
      this.afterLines = this.patch.diff_after.split('\n');
      this.processLineByLineDiff();
    }
  }

  processStructuredDiff(diff: StructuredDiff): void {
    this.diffLines = [];
    
    // Process removed lines
    diff.removed.forEach((line) => {
      this.diffLines.push({
        type: 'removed',
        beforeLine: line,
        afterLine: undefined,
      });
    });

    // Process added lines
    diff.added.forEach((line) => {
      this.diffLines.push({
        type: 'added',
        beforeLine: undefined,
        afterLine: line,
      });
    });

    // Process modified lines
    diff.modified.forEach((mod: ModifiedLine) => {
      this.diffLines.push({
        type: 'modified',
        beforeLine: mod.old,
        afterLine: mod.new,
        lineNumber: mod.line,
      });
    });

    // If no structured diff data, fall back to line-by-line
    if (this.diffLines.length === 0) {
      this.beforeLines = this.patch!.diff_before.split('\n');
      this.afterLines = this.patch!.diff_after.split('\n');
      this.processLineByLineDiff();
    }
  }

  processLineByLineDiff(): void {
    // Simple line-by-line comparison when structured diff is not available
    const maxLines = Math.max(this.beforeLines.length, this.afterLines.length);
    this.diffLines = [];

    for (let i = 0; i < maxLines; i++) {
      const before = this.beforeLines[i];
      const after = this.afterLines[i];

      if (before === undefined && after !== undefined) {
        this.diffLines.push({ type: 'added', afterLine: after });
      } else if (before !== undefined && after === undefined) {
        this.diffLines.push({ type: 'removed', beforeLine: before });
      } else if (before === after) {
        this.diffLines.push({ type: 'unchanged', beforeLine: before, afterLine: after });
      } else {
        this.diffLines.push({ type: 'modified', beforeLine: before, afterLine: after });
      }
    }
  }

  approvePatch(): void {
    if (!this.patch || this.approving) return;

    // Check if already applied
    if (this.patch.status === 'Applied') {
      this.toastService.info('This patch has already been applied.');
      return;
    }

    this.approving = true;
    // TODO: Get current user from auth service when user info endpoint is available
    const currentUser = 'Reviewer'; // Placeholder until user info is available

    this.patchesService.applyPatch(this.patch.id, { approved_by: currentUser }).subscribe({
      next: (updatedPatch) => {
        this.patch = updatedPatch;
        this.approving = false;
        this.toastService.success('Patch approved and applied successfully.');
        // Navigate back to run details after a short delay
        setTimeout(() => {
          if (this.runId) {
            this.router.navigate(['/runs', this.runId]);
          }
        }, 1500);
      },
      error: (err: any) => {
        this.approving = false;
        const errorMsg = err.error?.detail || err.message || 'Failed to approve patch';
        this.showError(errorMsg);
      },
    });
  }

  openRejectDialog(): void {
    this.showRejectDialog = true;
    this.rejectComment = '';
    // Focus comment input after dialog opens
    setTimeout(() => {
      this.commentInput?.nativeElement?.focus();
    }, 100);
  }

  closeRejectDialog(): void {
    this.showRejectDialog = false;
    this.rejectComment = '';
  }

  rejectPatch(): void {
    if (!this.patch || this.rejecting) return;

    this.rejecting = true;
    
    // TODO: Implement reject endpoint when available
    // For now, show a message that rejection is not yet implemented
    this.toastService.info('Reject functionality will be implemented in a future sprint.');
    this.rejecting = false;
    this.closeRejectDialog();
    
    // When reject endpoint is available, uncomment:
    /*
    this.patchesService.rejectPatch(this.patch.id, this.rejectComment).subscribe({
      next: () => {
        this.rejecting = false;
        this.closeRejectDialog();
        this.toastService.success('Patch rejected successfully.');
        setTimeout(() => {
          if (this.runId) {
            this.router.navigate(['/runs', this.runId]);
          }
        }, 1500);
      },
      error: (err: any) => {
        this.rejecting = false;
        const errorMsg = err.error?.detail || err.message || 'Failed to reject patch';
        this.showError(errorMsg);
      },
    });
    */
  }

  goBack(): void {
    if (this.runId) {
      this.router.navigate(['/runs', this.runId]);
    } else {
      this.router.navigate(['/dashboard']);
    }
  }

  showError(message: string): void {
    this.toastService.error(message);
  }

  formatTimestamp(timestamp: string | null): string {
    if (!timestamp) return 'N/A';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  }

  getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'applied':
        return 'primary';
      case 'proposed':
        return 'accent';
      case 'rejected':
        return 'warn';
      case 'error':
        return 'warn';
      default:
        return '';
    }
  }

  // Keyboard navigation (NFR-6)
  @HostListener('keydown', ['$event'])
  handleKeyboard(event: KeyboardEvent): void {
    // Escape key closes reject dialog
    if (event.key === 'Escape' && this.showRejectDialog) {
      this.closeRejectDialog();
      event.preventDefault();
      return;
    }

    // Ctrl/Cmd + Enter approves patch
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      if (!this.approving && this.patch?.status !== 'Applied') {
        this.approvePatch();
        event.preventDefault();
      }
    }

    // Tab navigation is handled by browser, but we ensure focus management
    if (event.key === 'Tab' && !this.showRejectDialog) {
      // Allow normal tab navigation
      return;
    }
  }

  // Focus management helpers (NFR-6)
  focusApproveButton(): void {
    setTimeout(() => {
      this.approveButton?.nativeElement?.focus();
    }, 0);
  }

  focusRejectButton(): void {
    setTimeout(() => {
      this.rejectButton?.nativeElement?.focus();
    }, 0);
  }
}

