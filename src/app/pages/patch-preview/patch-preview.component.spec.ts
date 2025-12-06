import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { flush } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { FormsModule } from '@angular/forms';

// Material modules
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { CommonModule } from '@angular/common';

import { PatchPreviewComponent } from './patch-preview.component';
import { PatchesService, Patch, StructuredDiff } from '../../services/patches.service';
import { ToastService } from '../../services/toast.service';
import { AuthService } from '../../services/auth.service';

describe('PatchPreviewComponent', () => {
  let component: PatchPreviewComponent;
  let fixture: ComponentFixture<PatchPreviewComponent>;
  let httpMock: HttpTestingController;
  let patchesService: PatchesService;
  let toastService: ToastService;
  let router: jasmine.SpyObj<Router>;
  let activatedRoute: any;

  const mockPatch: Patch = {
    id: 456,
    run_id: 123,
    page_id: '123456',
    diff_before: 'Original content\nLine 2\nLine 3',
    diff_after: 'Updated content\nLine 2 Modified\nLine 3\nNew line',
    diff_unified: '--- a/page\n+++ b/page\n@@ -1,3 +1,4 @@\n-Original content\n+Updated content\n Line 2\n-Line 3\n+Line 2 Modified\n+New line',
    diff_structured: {
      added: ['New line'],
      removed: ['Line 3'],
      modified: [
        { line: 1, old: 'Original content', new: 'Updated content' },
        { line: 2, old: 'Line 2', new: 'Line 2 Modified' }
      ]
    },
    approved_by: null,
    applied_at: null,
    status: 'Proposed',
    error_message: null
  };

  const mockAppliedPatch: Patch = {
    ...mockPatch,
    status: 'Applied',
    approved_by: 'Reviewer',
    applied_at: '2025-12-06T21:51:45Z'
  };

  beforeEach(async () => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    const routeParams = { runId: '123', patchId: '456' };

    await TestBed.configureTestingModule({
      declarations: [PatchPreviewComponent],
      imports: [
        CommonModule,
        FormsModule,
        HttpClientTestingModule,
        NoopAnimationsModule,
        MatCardModule,
        MatButtonModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatChipsModule,
        MatExpansionModule,
      ],
      providers: [
        PatchesService,
        ToastService,
        AuthService,
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of({
              get: (key: string) => routeParams[key as keyof typeof routeParams],
            }),
          },
        },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PatchPreviewComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    patchesService = TestBed.inject(PatchesService);
    toastService = TestBed.inject(ToastService);
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    activatedRoute = TestBed.inject(ActivatedRoute);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize and load patch on ngOnInit', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    expect(component.loading).toBe(true);
    expect(component.runId).toBe('123');
    expect(component.patchId).toBe('456');

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    expect(req.request.method).toBe('GET');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    expect(component.patch).toEqual(mockPatch);
    expect(component.loading).toBe(false);
    expect(component.error).toBeNull();
  }));

  it('should display loading spinner while fetching patch', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    expect(component.loading).toBe(true);
    const spinner = fixture.nativeElement.querySelector('mat-spinner');
    expect(spinner).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('Loading patch preview...');

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);
    tick();
  }));

  it('should handle error when loading patch fails', fakeAsync(() => {
    spyOn(toastService, 'error');
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(
      { detail: 'Patch not found' },
      { status: 404, statusText: 'Not Found' }
    );

    tick();
    fixture.detectChanges();

    expect(component.loading).toBe(false);
    expect(component.error).toBeTruthy();
    expect(toastService.error).toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Error Loading Patch');
  }));

  it('should process structured diff correctly', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    expect(component.diffLines.length).toBeGreaterThan(0);

    // Check that structured diff was processed
    const addedLines = component.diffLines.filter(line => line.type === 'added');
    const removedLines = component.diffLines.filter(line => line.type === 'removed');
    const modifiedLines = component.diffLines.filter(line => line.type === 'modified');

    expect(addedLines.length).toBeGreaterThan(0);
    expect(removedLines.length).toBeGreaterThan(0);
    expect(modifiedLines.length).toBeGreaterThan(0);

    // Verify modified line has both old and new content
    const modifiedLine = modifiedLines[0];
    expect(modifiedLine.beforeLine).toBe('Original content');
    expect(modifiedLine.afterLine).toBe('Updated content');
  }));

  it('should render diff lines in side-by-side view', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    // Check that diff panels are rendered
    const beforePanel = fixture.nativeElement.querySelector('.before-panel');
    const afterPanel = fixture.nativeElement.querySelector('.after-panel');

    expect(beforePanel).toBeTruthy();
    expect(afterPanel).toBeTruthy();

    // Check that diff lines are rendered
    const diffLines = fixture.nativeElement.querySelectorAll('.diff-line');
    expect(diffLines.length).toBeGreaterThan(0);
  }));

  it('should apply correct CSS classes for different line types', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    const diffLines = fixture.nativeElement.querySelectorAll('.diff-line');
    
    // Check for different line type classes
    const hasAdded = Array.from(diffLines).some((el: any) => 
      el.classList.contains('line-added')
    );
    const hasRemoved = Array.from(diffLines).some((el: any) => 
      el.classList.contains('line-removed')
    );
    const hasModified = Array.from(diffLines).some((el: any) => 
      el.classList.contains('line-modified-old') || el.classList.contains('line-modified-new')
    );

    expect(hasAdded || hasRemoved || hasModified).toBe(true);
  }));

  it('should fall back to line-by-line diff when structured diff is not available', fakeAsync(() => {
    const patchWithoutStructured: Patch = {
      ...mockPatch,
      diff_structured: null
    };

    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(patchWithoutStructured);

    tick();
    fixture.detectChanges();

    // Should still process diff using line-by-line comparison
    expect(component.diffLines.length).toBeGreaterThan(0);
    expect(component.beforeLines.length).toBeGreaterThan(0);
    expect(component.afterLines.length).toBeGreaterThan(0);
  }));

  it('should display patch information correctly', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('456'); // Patch ID
    expect(fixture.nativeElement.textContent).toContain('123456'); // Page ID
    expect(fixture.nativeElement.textContent).toContain('Proposed'); // Status
  }));

  it('should show approve and reject buttons for proposed patches', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
    const rejectButton = fixture.nativeElement.querySelector('button[aria-label="Reject patch"]');

    expect(approveButton).toBeTruthy();
    expect(rejectButton).toBeTruthy();
    expect(approveButton.textContent).toContain('Approve & Apply');
  }));

  it('should hide action buttons for applied patches', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockAppliedPatch);

    tick();
    fixture.detectChanges();

    const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
    const rejectButton = fixture.nativeElement.querySelector('button[aria-label="Reject patch"]');

    expect(approveButton).toBeFalsy();
    expect(rejectButton).toBeFalsy();
    expect(fixture.nativeElement.textContent).toContain('This patch has been applied');
  }));

  it('should approve patch successfully', fakeAsync(() => {
    spyOn(toastService, 'success');
    fixture.detectChanges();
    tick();

    const req1 = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req1.flush(mockPatch);

    tick();
    fixture.detectChanges();

    // Click approve button
    const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
    approveButton.click();
    tick();

    expect(component.approving).toBe(true);

    const req2 = httpMock.expectOne((request) => {
      return request.url === 'http://localhost:8000/api/v1/patches/456/apply' &&
             request.method === 'POST';
    });
    req2.flush(mockAppliedPatch);

    tick(1500); // Wait for navigation delay
    fixture.detectChanges();

    expect(component.approving).toBe(false);
    expect(component.patch?.status).toBe('Applied');
    expect(toastService.success).toHaveBeenCalledWith('Patch approved and applied successfully.');
    expect(router.navigate).toHaveBeenCalledWith(['/runs', '123']);
  }));

  it('should not approve already applied patch', fakeAsync(() => {
    spyOn(toastService, 'info');
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockAppliedPatch);

    tick();
    fixture.detectChanges();

    // Try to approve (should be prevented)
    component.approvePatch();
    tick();

    expect(toastService.info).toHaveBeenCalledWith('This patch has already been applied.');
  }));

  it('should handle approve error gracefully', fakeAsync(() => {
    spyOn(toastService, 'error');
    fixture.detectChanges();
    tick();

    const req1 = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req1.flush(mockPatch);

    tick();
    fixture.detectChanges();

    // Click approve button
    const approveButton = fixture.nativeElement.querySelector('button[aria-label="Approve patch"]');
    approveButton.click();
    tick();

    // Match request with query parameters
    const req2 = httpMock.expectOne((request) => {
      return request.url === 'http://localhost:8000/api/v1/patches/456/apply' &&
             request.method === 'POST';
    });
    req2.flush(
      { detail: 'Failed to apply patch' },
      { status: 500, statusText: 'Internal Server Error' }
    );

    tick();
    fixture.detectChanges();

    expect(component.approving).toBe(false);
    expect(toastService.error).toHaveBeenCalled();
  }));

  it('should open reject dialog when reject button is clicked', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    const rejectButton = fixture.nativeElement.querySelector('button[aria-label="Reject patch"]');
    rejectButton.click();
    tick(100); // Flush setTimeout for focus
    fixture.detectChanges();

    expect(component.showRejectDialog).toBe(true);
    const dialog = fixture.nativeElement.querySelector('.reject-dialog');
    expect(dialog).toBeTruthy();
  }));

  it('should close reject dialog when cancel is clicked', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    // Open dialog
    component.openRejectDialog();
    tick(100); // Flush setTimeout for focus
    fixture.detectChanges();

    // Close dialog
    component.closeRejectDialog();
    fixture.detectChanges();

    expect(component.showRejectDialog).toBe(false);
    expect(component.rejectComment).toBe('');
  }));

  it('should handle keyboard escape key to close dialog', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    component.showRejectDialog = true;
    fixture.detectChanges();

    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    component.handleKeyboard(event);

    expect(component.showRejectDialog).toBe(false);
  }));

  it('should handle Ctrl+Enter to approve patch', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req1 = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req1.flush(mockPatch);

    tick();
    fixture.detectChanges();

    const event = new KeyboardEvent('keydown', {
      key: 'Enter',
      ctrlKey: true
    });
    component.handleKeyboard(event);
    tick();

    // Match request with query parameters
    const req2 = httpMock.expectOne((request) => {
      return request.url === 'http://localhost:8000/api/v1/patches/456/apply' &&
             request.method === 'POST';
    });
    req2.flush(mockAppliedPatch);

    tick(); // Process the response
    tick(2000); // Flush navigation delay timer (1500ms) and any other pending timers
    fixture.detectChanges();
    
    // Ensure all timers are flushed
    try {
      flush(); // This will throw if there are no more timers, which is fine
    } catch (e) {
      // Expected - no more timers to flush
    }
  }));

  it('should not approve with Ctrl+Enter if patch is already applied', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockAppliedPatch);

    tick();
    fixture.detectChanges();

    const approveSpy = spyOn(component, 'approvePatch');
    const event = new KeyboardEvent('keydown', {
      key: 'Enter',
      ctrlKey: true
    });
    component.handleKeyboard(event);

    expect(approveSpy).not.toHaveBeenCalled();
  }));

  it('should navigate back when back button is clicked', () => {
    component.runId = '123';
    component.goBack();

    expect(router.navigate).toHaveBeenCalledWith(['/runs', '123']);
  });

  it('should navigate to dashboard if runId is not available', () => {
    component.runId = null;
    component.goBack();

    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
  });

  it('should format timestamp correctly', () => {
    const timestamp = '2025-12-06T21:51:45Z';
    const formatted = component.formatTimestamp(timestamp);
    expect(formatted).toBeTruthy();
    expect(typeof formatted).toBe('string');
  });

  it('should return "N/A" for null timestamp', () => {
    const formatted = component.formatTimestamp(null);
    expect(formatted).toBe('N/A');
  });

  it('should get correct status color', () => {
    expect(component.getStatusColor('Applied')).toBe('primary');
    expect(component.getStatusColor('Proposed')).toBe('accent');
    expect(component.getStatusColor('Rejected')).toBe('warn');
    expect(component.getStatusColor('ERROR')).toBe('warn');
  });

  it('should display raw content in expandable sections', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    const expansionPanels = fixture.nativeElement.querySelectorAll('mat-expansion-panel');
    expect(expansionPanels.length).toBeGreaterThan(0);

    // Check for raw content sections
    expect(fixture.nativeElement.textContent).toContain('Before Content');
    expect(fixture.nativeElement.textContent).toContain('After Content');
  }));

  it('should unsubscribe on destroy', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(mockPatch);

    tick();
    fixture.detectChanges();

    const unsubscribeSpy = spyOn(component['routeSubscription']!, 'unsubscribe');
    component.ngOnDestroy();
    expect(unsubscribeSpy).toHaveBeenCalled();
  }));

  it('should handle missing patchId in route', () => {
    const routeWithoutPatchId = {
      paramMap: of({
        get: (key: string) => key === 'runId' ? '123' : null,
      }),
    };

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      declarations: [PatchPreviewComponent],
      imports: [
        CommonModule,
        FormsModule,
        HttpClientTestingModule,
        NoopAnimationsModule,
        MatCardModule,
        MatButtonModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatChipsModule,
        MatExpansionModule,
      ],
      providers: [
        PatchesService,
        ToastService,
        AuthService,
        { provide: ActivatedRoute, useValue: routeWithoutPatchId },
        { provide: Router, useValue: router },
      ],
    });

    const newFixture = TestBed.createComponent(PatchPreviewComponent);
    const newComponent = newFixture.componentInstance;
    spyOn(newComponent, 'showError');

    newFixture.detectChanges();

    expect(newComponent.error).toBeTruthy();
    expect(newComponent.showError).toHaveBeenCalled();
  });

  it('should display error message when patch has error status', fakeAsync(() => {
    const errorPatch: Patch = {
      ...mockPatch,
      status: 'ERROR',
      error_message: { error: 'Confluence API error', type: 'ConnectionError' }
    };

    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/patches/456');
    req.flush(errorPatch);

    tick();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Error');
    expect(fixture.nativeElement.querySelector('.error-message')).toBeTruthy();
  }));
});

