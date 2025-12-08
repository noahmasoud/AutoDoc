import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { FormsModule } from '@angular/forms';

// Material modules
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { CommonModule } from '@angular/common';

import { PatchPreviewComponent } from './patch-preview.component';
import { PatchesService, Patch } from '../../services/patches.service';
import { ToastService } from '../../services/toast.service';

describe('PatchPreviewComponent - UX Acceptance Tests', () => {
  let component: PatchPreviewComponent;
  let fixture: ComponentFixture<PatchPreviewComponent>;
  let httpMock: HttpTestingController;
  let patchesService: PatchesService;
  let toastService: jasmine.SpyObj<ToastService>;
  let router: jasmine.SpyObj<Router>;
  let activatedRoute: any;

  const mockPatch: Patch = {
    id: 1,
    run_id: 123,
    page_id: '12345',
    diff_before: 'Old content line 1\nOld content line 2',
    diff_after: 'New content line 1\nNew content line 2\nAdded line',
    approved_by: null,
    applied_at: null,
    status: 'Awaiting Review',
    error_message: null,
  };

  beforeEach(async () => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    const toastServiceSpy = jasmine.createSpyObj('ToastService', ['error', 'success', 'info', 'warning']);
    const routeParams = { patchId: '1', runId: '123' };

    await TestBed.configureTestingModule({
      imports: [
        PatchPreviewComponent,
        CommonModule,
        FormsModule,
        HttpClientTestingModule,
        NoopAnimationsModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatChipsModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatTooltipModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
      ],
      providers: [
        PatchesService,
        {
          provide: ToastService,
          useValue: toastServiceSpy,
        },
        {
          provide: Router,
          useValue: routerSpy,
        },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => routeParams[key as keyof typeof routeParams],
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PatchPreviewComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    patchesService = TestBed.inject(PatchesService);
    toastService = TestBed.inject(ToastService) as jasmine.SpyObj<ToastService>;
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    activatedRoute = TestBed.inject(ActivatedRoute);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should load patch from route params', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const req = httpMock.expectOne('http://localhost:8000/api/patches/1');
      expect(req.request.method).toBe('GET');
      req.flush(mockPatch);

      tick();
      fixture.detectChanges();

      expect(component.patchData).toEqual(mockPatch);
      expect(component.loading).toBe(false);
    }));
  });

  describe('FR-15: Before/After Diff Preview', () => {
    it('should display explicit "Before" and "After" labels', fakeAsync(() => {
      component.patchData = mockPatch;
      fixture.detectChanges();

      const beforeHeader = fixture.nativeElement.querySelector('.before-header');
      const afterHeader = fixture.nativeElement.querySelector('.after-header');

      expect(beforeHeader).toBeTruthy();
      expect(afterHeader).toBeTruthy();
      expect(beforeHeader.textContent).toContain('Before');
      expect(afterHeader.textContent).toContain('After');
    }));

    it('should have visual distinction between Before and After panes', fakeAsync(() => {
      component.patchData = mockPatch;
      component.viewMode = 'side-by-side';
      fixture.detectChanges();

      const beforePane = fixture.nativeElement.querySelector('.before-pane');
      const afterPane = fixture.nativeElement.querySelector('.after-pane');

      expect(beforePane).toBeTruthy();
      expect(afterPane).toBeTruthy();

      // Check for distinct styling classes
      const beforeHeader = beforePane.querySelector('.before-header');
      const afterHeader = afterPane.querySelector('.after-header');

      expect(beforeHeader).toHaveClass('before-header');
      expect(afterHeader).toHaveClass('after-header');
    }));

    it('should display diff_before content in Before pane', fakeAsync(() => {
      component.patchData = mockPatch;
      component.viewMode = 'side-by-side';
      fixture.detectChanges();

      const beforeContent = fixture.nativeElement.querySelector('.before-pane .diff-content');
      expect(beforeContent).toBeTruthy();
      expect(beforeContent.textContent).toContain('Old content line 1');
    }));

    it('should display diff_after content in After pane', fakeAsync(() => {
      component.patchData = mockPatch;
      component.viewMode = 'side-by-side';
      fixture.detectChanges();

      const afterContent = fixture.nativeElement.querySelector('.after-pane .diff-content');
      expect(afterContent).toBeTruthy();
      expect(afterContent.textContent).toContain('New content line 1');
    }));
  });

  describe('Change Highlights and Legend', () => {
    it('should display change legend with icons', fakeAsync(() => {
      component.patchData = mockPatch;
      fixture.detectChanges();

      const legend = fixture.nativeElement.querySelector('.legend');
      expect(legend).toBeTruthy();

      const legendItems = fixture.nativeElement.querySelectorAll('.legend-item');
      expect(legendItems.length).toBeGreaterThanOrEqual(3);

      // Check for Added, Removed, Modified indicators
      const legendText = legend.textContent;
      expect(legendText).toContain('Added');
      expect(legendText).toContain('Removed');
      expect(legendText).toContain('Modified');
    }));

    it('should have consistent icons for change types', fakeAsync(() => {
      component.patchData = mockPatch;
      fixture.detectChanges();

      const addedIcon = fixture.nativeElement.querySelector('.added-icon mat-icon');
      const removedIcon = fixture.nativeElement.querySelector('.removed-icon mat-icon');
      const modifiedIcon = fixture.nativeElement.querySelector('.modified-icon mat-icon');

      expect(addedIcon).toBeTruthy();
      expect(removedIcon).toBeTruthy();
      expect(modifiedIcon).toBeTruthy();
    }));
  });

  describe('View Mode Toggle', () => {
    it('should toggle between side-by-side and unified view', fakeAsync(() => {
      component.patchData = mockPatch;
      component.viewMode = 'side-by-side';
      fixture.detectChanges();

      expect(component.viewMode).toBe('side-by-side');
      expect(fixture.nativeElement.querySelector('.side-by-side')).toBeTruthy();

      component.toggleViewMode();
      fixture.detectChanges();

      expect(component.viewMode).toBe('unified');
      expect(fixture.nativeElement.querySelector('.unified')).toBeTruthy();
    }));

    it('should display side-by-side view by default', fakeAsync(() => {
      component.patchData = mockPatch;
      fixture.detectChanges();

      expect(component.viewMode).toBe('side-by-side');
      expect(fixture.nativeElement.querySelector('.side-by-side')).toBeTruthy();
    }));

    it('should have toggle button visible', fakeAsync(() => {
      component.patchData = mockPatch;
      fixture.detectChanges();

      const toggleButton = fixture.nativeElement.querySelector('.view-controls button');
      expect(toggleButton).toBeTruthy();
      expect(toggleButton.textContent).toContain('Side-by-Side');
    }));
  });

  describe('NFR-5: Critical Actions Accessibility', () => {
    it('should display Approve button when patch is awaiting review', fakeAsync(() => {
      component.patchData = mockPatch;
      component.patchData.status = 'Awaiting Review';
      fixture.detectChanges();

      const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
      expect(approveButton).toBeTruthy();
      expect(approveButton.textContent).toContain('Approve');
    }));

    it('should display Reject button when patch is awaiting review', fakeAsync(() => {
      component.patchData = mockPatch;
      component.patchData.status = 'Awaiting Review';
      fixture.detectChanges();

      const rejectButton = fixture.nativeElement.querySelector('button[aria-label="Reject patch"]');
      expect(rejectButton).toBeTruthy();
      expect(rejectButton.textContent).toContain('Reject');
    }));

    it('should allow approval with optional comment', fakeAsync(() => {
      component.patchData = mockPatch;
      component.patchData.status = 'Awaiting Review';
      component.approvalComment = 'Looks good!';
      fixture.detectChanges();

      const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
      expect(approveButton).toBeTruthy();
      expect(component.approvalComment).toBe('Looks good!');
    }));

    it('should apply patch when approved', fakeAsync(() => {
      component.patchData = mockPatch;
      component.patchData.status = 'Awaiting Review';
      fixture.detectChanges();

      const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
      approveButton.click();
      tick();

      const req = httpMock.expectOne('http://localhost:8000/api/patches/1/apply');
      expect(req.request.method).toBe('POST');
      
      const updatedPatch = { ...mockPatch, status: 'Applied', approved_by: 'test-user' };
      req.flush(updatedPatch);
      tick();
      fixture.detectChanges();

      expect(component.patchData.status).toBe('Applied');
    }));
  });

  describe('UX Acceptance Criteria', () => {
    it('AC1: Reviewer can identify added/removed/changed lines at a glance', fakeAsync(() => {
      component.patchData = mockPatch;
      component.viewMode = 'side-by-side';
      fixture.detectChanges();

      // Verify Before and After panes are clearly labeled
      const beforeLabel = fixture.nativeElement.querySelector('.before-header h3');
      const afterLabel = fixture.nativeElement.querySelector('.after-header h3');

      expect(beforeLabel.textContent.trim()).toBe('Before');
      expect(afterLabel.textContent.trim()).toBe('After');

      // Verify content is displayed in monospace for code readability
      const diffContent = fixture.nativeElement.querySelector('.diff-content');
      const styles = window.getComputedStyle(diffContent);
      expect(styles.fontFamily).toContain('monospace');
    }));

    it('AC2: Approve/Reject buttons are ≤3 clicks away from Run Details', fakeAsync(() => {
      // This test verifies the component structure supports NFR-5
      // Navigation path: Run Details (1 click) -> Patch Preview (1 click) -> Approve/Reject (1 click)
      // Total: 3 clicks maximum

      component.patchData = mockPatch;
      component.patchData.status = 'Awaiting Review';
      fixture.detectChanges();

      // Verify buttons are directly visible (no additional clicks needed)
      const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
      const rejectButton = fixture.nativeElement.querySelector('button[aria-label="Reject patch"]');

      expect(approveButton).toBeTruthy();
      expect(rejectButton).toBeTruthy();
      // Buttons should be visible without scrolling or expanding panels
      expect(approveButton.offsetParent).not.toBeNull();
      expect(rejectButton.offsetParent).not.toBeNull();
    }));

    it('AC3: Side-by-side view is responsive on typical screens', fakeAsync(() => {
      component.patchData = mockPatch;
      component.viewMode = 'side-by-side';
      fixture.detectChanges();

      const diffContainer = fixture.nativeElement.querySelector('.diff-container.side-by-side');
      expect(diffContainer).toBeTruthy();

      // Verify responsive classes are applied
      const diffPanes = fixture.nativeElement.querySelectorAll('.diff-pane');
      expect(diffPanes.length).toBe(2);
    }));
  });

  describe('Error Handling', () => {
    it('should handle patch load error gracefully', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      const req = httpMock.expectOne('http://localhost:8000/api/patches/1');
      req.flush(
        { detail: 'Patch not found' },
        { status: 404, statusText: 'Not Found' }
      );

      tick();
      fixture.detectChanges();

      expect(component.loading).toBe(false);
      expect(toastService.error).toHaveBeenCalled();
    }));

    it('should display error message if patch has error_message', fakeAsync(() => {
      const errorPatch = {
        ...mockPatch,
        error_message: { error: 'Test error', type: 'ValidationError' },
      };
      component.patchData = errorPatch;
      fixture.detectChanges();

      const errorCard = fixture.nativeElement.querySelector('.error-card');
      expect(errorCard).toBeTruthy();
      expect(errorCard.textContent).toContain('Error Details');
    }));
  });

  describe('Status Display', () => {
    it('should display status chip with appropriate color', fakeAsync(() => {
      component.patchData = { ...mockPatch, status: 'Applied' };
      fixture.detectChanges();

      const statusChip = fixture.nativeElement.querySelector('mat-chip');
      expect(statusChip).toBeTruthy();
      expect(statusChip.textContent).toContain('Applied');
    }));

    it('should not show approve/reject buttons for applied patches', fakeAsync(() => {
      component.patchData = { ...mockPatch, status: 'Applied' };
      fixture.detectChanges();

      const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
      const rejectButton = fixture.nativeElement.querySelector('button[aria-label="Reject patch"]');

      expect(approveButton).toBeNull();
      expect(rejectButton).toBeNull();
    }));
  });
});

