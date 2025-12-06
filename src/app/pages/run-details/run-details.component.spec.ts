import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';

// Material modules
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';

import { RunDetailsComponent } from './run-details.component';
import { ChangeReportService, ChangeReport } from '../../services/change-report.service';
import { ToastService } from '../../services/toast.service';

describe('RunDetailsComponent', () => {
  let component: RunDetailsComponent;
  let fixture: ComponentFixture<RunDetailsComponent>;
  let httpMock: HttpTestingController;
  let changeReportService: ChangeReportService;
  let snackBar: jasmine.SpyObj<MatSnackBar>;
  let activatedRoute: any;

  const mockChangeReport: ChangeReport = {
    run_id: '123',
    timestamp: '2024-01-15T10:30:00Z',
    diff_summary: {
      'test-file.py': {
        added: ['line1', 'line2'],
        removed: ['old-line'],
        modified: [
          { line: 5, old: 'old code', new: 'new code' },
        ],
      },
      'another-file.ts': {
        added: ['new line'],
        removed: [],
        modified: [],
      },
    },
    analyzer_findings: {
      'test-file.py': [
        {
          symbol: 'testFunction',
          type: 'added',
          severity: 'info',
          message: 'New function added',
        },
      ],
    },
  };

  beforeEach(async () => {
    const snackBarSpy = jasmine.createSpyObj('MatSnackBar', ['open']);
    const toastServiceSpy = jasmine.createSpyObj('ToastService', ['error', 'success', 'info']);
    const routeParams = { runId: '123' };

    await TestBed.configureTestingModule({
      declarations: [RunDetailsComponent],
      imports: [
        CommonModule,
        FormsModule,
        HttpClientTestingModule,
        NoopAnimationsModule,
        MatCardModule,
        MatExpansionModule,
        MatChipsModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
      ],
      providers: [
        ChangeReportService,
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of({
              get: (key: string) => routeParams[key as keyof typeof routeParams],
            }),
          },
        },
        { provide: MatSnackBar, useValue: snackBarSpy },
        { provide: ToastService, useValue: toastServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RunDetailsComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    changeReportService = TestBed.inject(ChangeReportService);
    snackBar = TestBed.inject(MatSnackBar) as jasmine.SpyObj<MatSnackBar>;
    activatedRoute = TestBed.inject(ActivatedRoute);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display loading spinner while fetching', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    expect(component.loading).toBe(true);
    const spinner = fixture.nativeElement.querySelector('mat-spinner');
    expect(spinner).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('Loading run details...');
    
    // Complete the request
    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    req.flush(mockChangeReport);
    tick();
  }));

  it('should render run ID and timestamp from mock data', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    expect(req.request.method).toBe('GET');
    req.flush(mockChangeReport);

    tick();
    fixture.detectChanges();

    expect(component.report).toEqual(mockChangeReport);
    expect(component.loading).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('123');
    expect(fixture.nativeElement.textContent).toContain('Run ID:');
    expect(fixture.nativeElement.textContent).toContain('Timestamp:');
  }));

  it('should expand/collapse file diff panels', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    req.flush(mockChangeReport);

    tick();
    fixture.detectChanges();

    const expansionPanels = fixture.nativeElement.querySelectorAll('mat-expansion-panel');
    expect(expansionPanels.length).toBeGreaterThan(0);

    // Test expansion panel interaction
    const firstPanel = expansionPanels[0];
    const header = firstPanel.querySelector('mat-expansion-panel-header');
    
    expect(header).toBeTruthy();
    // Click to expand
    header.click();
    tick();
    fixture.detectChanges();

    // Panel should be expanded (content visible)
    const content = firstPanel.querySelector('.diff-content');
    expect(content).toBeTruthy();
  }));

  it('should filter results by filename', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    req.flush(mockChangeReport);

    tick();
    fixture.detectChanges();

    // Set search query
    component.searchQuery = 'test-file';
    component.onSearchChange();
    fixture.detectChanges();

    expect(component.filteredFileDiffs.length).toBe(1);
    expect(component.filteredFileDiffs[0].fileName).toBe('test-file.py');

    // Clear filter
    component.searchQuery = '';
    component.onSearchChange();
    fixture.detectChanges();

    expect(component.filteredFileDiffs.length).toBe(2);
  }));

  it('should handle error response gracefully', fakeAsync(() => {
    const toastService = TestBed.inject(ToastService) as jasmine.SpyObj<ToastService>;
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    req.flush(
      { detail: 'Run not found' },
      { status: 404, statusText: 'Not Found' }
    );

    tick();
    fixture.detectChanges();

    expect(component.loading).toBe(false);
    expect(component.error).toBeTruthy();
    expect(toastService.error).toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Error Loading Run Details');
  }));

  it('should parse report data correctly', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    req.flush(mockChangeReport);

    tick();
    fixture.detectChanges();

    expect(component.fileDiffs.length).toBe(2);
    expect(component.fileDiffs[0].fileName).toBe('test-file.py');
    expect(component.findingsByFile['test-file.py']).toBeDefined();
    expect(component.findingsByFile['test-file.py'].length).toBe(1);
  }));

  it('should format timestamp correctly', () => {
    const timestamp = '2024-01-15T10:30:00Z';
    const formatted = component.formatTimestamp(timestamp);
    expect(formatted).toBeTruthy();
    expect(typeof formatted).toBe('string');
  });

  it('should unsubscribe on destroy', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // Handle the HTTP request
    const req = httpMock.expectOne('http://localhost:8000/api/v1/runs/123/report');
    req.flush(mockChangeReport);

    tick();
    fixture.detectChanges();

    const unsubscribeSpy = spyOn(component['routeSubscription']!, 'unsubscribe');
    component.ngOnDestroy();
    expect(unsubscribeSpy).toHaveBeenCalled();
  }));
});

