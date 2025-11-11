import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { CommonModule } from '@angular/common';
import { MatChipsModule } from '@angular/material/chips';
import { AnalyzerFindingsComponent } from './analyzer-findings.component';
import { AnalyzerFinding } from '../../services/change-report.service';

describe('AnalyzerFindingsComponent', () => {
  let component: AnalyzerFindingsComponent;
  let fixture: ComponentFixture<AnalyzerFindingsComponent>;

  const mockFindings: Record<string, AnalyzerFinding[]> = {
    'test-file.py': [
      {
        symbol: 'testFunction',
        type: 'added',
        severity: 'info',
        message: 'New function added',
      },
      {
        symbol: 'oldFunction',
        type: 'removed',
        severity: 'warning',
        message: 'Function removed',
      },
    ],
    'another-file.ts': [
      {
        symbol: 'modifiedFunction',
        type: 'modified',
        severity: 'error',
        message: 'Function signature changed',
      },
    ],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AnalyzerFindingsComponent],
      imports: [
        CommonModule,
        NoopAnimationsModule,
        MatChipsModule,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AnalyzerFindingsComponent);
    component = fixture.componentInstance;
    component.findingsByFile = mockFindings;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should group findings by file', () => {
    fixture.detectChanges();

    const fileNames = Object.keys(component.findingsByFile);
    expect(fileNames.length).toBe(2);
    expect(fileNames).toContain('test-file.py');
    expect(fileNames).toContain('another-file.ts');
    expect(component.findingsByFile['test-file.py'].length).toBe(2);
    expect(component.findingsByFile['another-file.ts'].length).toBe(1);
  });

  it('should render chips with correct colors for added type', () => {
    fixture.detectChanges();

    const finding = component.findingsByFile['test-file.py'][0];
    const color = component.getChangeTypeColor(finding.type);
    expect(color).toBe('primary');
  });

  it('should render chips with correct colors for removed type', () => {
    fixture.detectChanges();

    const finding = component.findingsByFile['test-file.py'][1];
    const color = component.getChangeTypeColor(finding.type);
    expect(color).toBe('warn');
  });

  it('should render chips with correct colors for modified type', () => {
    fixture.detectChanges();

    const finding = component.findingsByFile['another-file.ts'][0];
    const color = component.getChangeTypeColor(finding.type);
    expect(color).toBe('accent');
  });

  it('should display correct symbol text', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    expect(compiled.textContent).toContain('testFunction');
    expect(compiled.textContent).toContain('oldFunction');
    expect(compiled.textContent).toContain('modifiedFunction');
  });

  it('should display correct detail text', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    expect(compiled.textContent).toContain('New function added');
    expect(compiled.textContent).toContain('Function removed');
    expect(compiled.textContent).toContain('Function signature changed');
  });

  it('should render chips with correct severity colors', () => {
    fixture.detectChanges();

    const errorFinding = component.findingsByFile['another-file.ts'][0];
    const errorColor = component.getSeverityColor(errorFinding.severity);
    expect(errorColor).toBe('warn'); // error severity maps to 'warn' color

    const warningFinding = component.findingsByFile['test-file.py'][1];
    const warningColor = component.getSeverityColor(warningFinding.severity);
    expect(warningColor).toBe('accent'); // warning severity maps to 'accent' color
  });

  it('should handle empty findings gracefully', () => {
    component.findingsByFile = {};
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    // Component should not crash and should handle empty state
    expect(component).toBeTruthy();
  });

  it('should render file names correctly', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    const fileNames = compiled.querySelectorAll('.file-name');
    expect(fileNames.length).toBe(2);
    expect(fileNames[0].textContent).toContain('test-file.py');
    expect(fileNames[1].textContent).toContain('another-file.ts');
  });

  it('should render all finding items', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    const findingItems = compiled.querySelectorAll('.finding-item');
    // Should have 3 total findings (2 in test-file.py, 1 in another-file.ts)
    expect(findingItems.length).toBe(3);
  });

  it('should handle missing optional fields', () => {
    const findingsWithMissingFields: Record<string, AnalyzerFinding[]> = {
      'test-file.py': [
        {
          message: 'Finding without symbol or type',
        },
      ],
    };

    component.findingsByFile = findingsWithMissingFields;
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    expect(compiled.textContent).toContain('Finding without symbol or type');
    // Should not crash when optional fields are missing
    expect(component).toBeTruthy();
  });
});

