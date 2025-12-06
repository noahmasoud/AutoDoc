import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';

// Angular Material modules
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { PatchesService, Patch } from '../../services/patches.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-patch-preview',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './patch-preview.component.html',
  styleUrls: ['./patch-preview.component.css'],
})
export class PatchPreviewComponent implements OnInit {
  @Input() patchId?: number;
  @Input() patch?: Patch;
  @Input() runId?: number;

  viewMode: 'side-by-side' | 'unified' = 'side-by-side';
  patchData: Patch | null = null;
  loading = false;
  processing = false;
  approvalComment = '';

  constructor(
    private patchesService: PatchesService,
    private toastService: ToastService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    if (this.patch) {
      this.patchData = this.patch;
    } else {
      // Try to get patchId from route params if not provided as input
      const routePatchId = this.route.snapshot.paramMap.get('patchId');
      const routeRunId = this.route.snapshot.paramMap.get('runId');
      
      if (routePatchId) {
        this.patchId = parseInt(routePatchId, 10);
        if (routeRunId) {
          this.runId = parseInt(routeRunId, 10);
        }
      }
      
      if (this.patchId) {
        this.loadPatch(this.patchId);
      } else if (!this.patch) {
        this.toastService.error('Patch ID not provided');
      }
    }
  }

  loadPatch(patchId: number): void {
    this.loading = true;
    this.patchesService.getPatch(patchId).subscribe({
      next: (patch) => {
        this.patchData = patch;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.toastService.error(`Failed to load patch: ${err.message}`);
      },
    });
  }

  toggleViewMode(): void {
    this.viewMode = this.viewMode === 'side-by-side' ? 'unified' : 'side-by-side';
  }

  approvePatch(): void {
    if (!this.patchData) return;

    this.processing = true;
    this.patchesService.applyPatch(this.patchData.id, this.approvalComment || undefined).subscribe({
      next: (updatedPatch) => {
        this.patchData = updatedPatch;
        this.processing = false;
        this.toastService.success('Patch approved and applied successfully');
        // Optionally navigate back to run details
        if (this.runId) {
          setTimeout(() => {
            this.router.navigate(['/runs', this.runId]);
          }, 1500);
        }
      },
      error: (err) => {
        this.processing = false;
        this.toastService.error(`Failed to apply patch: ${err.message}`);
      },
    });
  }

  rejectPatch(): void {
    if (!this.patchData) return;
    // For now, rejection is just a UI action - could be extended to update status
    this.toastService.info('Patch rejected (status update not yet implemented)');
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

  canApprove(): boolean {
    return this.patchData?.status === 'Awaiting Review' && !this.processing;
  }

  canReject(): boolean {
    return this.patchData?.status === 'Awaiting Review' && !this.processing;
  }
}

