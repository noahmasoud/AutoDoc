import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { ChangeReport } from './change-report.service';

/**
 * Mock service for loading change report from local JSON file.
 * Used for offline development and testing when backend is unavailable.
 */
@Injectable({
  providedIn: 'root',
})
export class MockChangeReportService {
  private readonly mockDataPath = 'assets/mock-data/change_report.json';

  constructor(private http: HttpClient) {}

  /**
   * Loads mock change report from local JSON file.
   *
   * @param runId The run identifier (ignored for mock, but kept for API compatibility)
   * @returns Observable of ChangeReport
   */
  getRunReport(runId: string): Observable<ChangeReport> {
    return this.http.get<ChangeReport>(this.mockDataPath).pipe(
      map((data) => {
        // Optionally update run_id to match requested runId
        return {
          ...data,
          run_id: runId || data.run_id,
        };
      }),
      catchError((error) => {
        console.warn('Failed to load mock change report:', error);
        // Return a default mock report if file loading fails
        return of(this.getDefaultMockReport(runId));
      })
    );
  }

  /**
   * Returns a default mock report if JSON file cannot be loaded.
   *
   * @param runId The run identifier
   * @returns Default ChangeReport
   */
  private getDefaultMockReport(runId: string): ChangeReport {
    return {
      run_id: runId || 'run_001',
      timestamp: new Date().toISOString(),
      diff_summary: {
        'backend/diff_parser.py': {
          added: ['def new_func(): pass'],
          removed: [],
          modified: [],
        },
      },
      analyzer_findings: {
        'backend/diff_parser.py': [
          {
            type: 'added',
            symbol: 'new_func',
            severity: 'info',
            message: 'Added new function',
          },
        ],
      },
    };
  }
}

