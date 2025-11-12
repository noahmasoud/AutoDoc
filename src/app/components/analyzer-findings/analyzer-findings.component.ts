import { Component, Input } from '@angular/core';
import { AnalyzerFinding } from '../../services/change-report.service';

@Component({
  selector: 'app-analyzer-findings',
  standalone: false,
  templateUrl: './analyzer-findings.component.html',
  styleUrls: ['./analyzer-findings.component.css'],
})
export class AnalyzerFindingsComponent {
  @Input() findingsByFile: Record<string, AnalyzerFinding[]> = {};

  getSeverityColor(severity?: string): string {
    if (!severity) return '';
    const sev = severity.toLowerCase();
    if (sev === 'error') return 'warn';
    if (sev === 'warning') return 'accent';
    return '';
  }

  getChangeTypeColor(changeType?: string): string {
    if (!changeType) return '';
    const type = changeType.toLowerCase();
    if (type === 'added') return 'primary';
    if (type === 'removed') return 'warn';
    if (type === 'modified') return 'accent';
    return '';
  }
}

