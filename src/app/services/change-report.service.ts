import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

/**
 * Interface for diff result containing added, removed, and modified lines.
 */
export interface DiffResult {
  added: string[];
  removed: string[];
  modified: { line: number; old: string; new: string }[];
}

/**
 * Interface for analyzer finding.
 */
export interface AnalyzerFinding {
  file?: string;
  symbol?: string;
  type?: string;
  severity?: string;
  message?: string;
  [key: string]: unknown;
}

/**
 * Interface for change report response from backend.
 */
export interface ChangeReport {
  run_id: string;
  timestamp: string;
  diff_summary: Record<string, DiffResult>;
  analyzer_findings: Record<string, AnalyzerFinding[]>;
}

/**
 * Request body for diff parsing endpoint.
 */
interface DiffRequest {
  old_file: string;
  new_file: string;
}

/**
 * Service for communicating with change report and diff parsing APIs.
 */
@Injectable({
  providedIn: 'root',
})
export class ChangeReportService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Retrieves the change report for a specific run.
   *
   * @param runId The run identifier
   * @returns Observable of ChangeReport
   */
  getRunReport(runId: string): Observable<ChangeReport> {
    const url = `${this.apiUrl}/v1/runs/${runId}/report`;
    return this.http.get<ChangeReport>(url).pipe(
      catchError((error: HttpErrorResponse) => {
        return this.handleError(error, `Failed to fetch run report for run ${runId}`);
      })
    );
  }

  /**
   * Parses differences between two file contents.
   *
   * @param oldFile The original file content
   * @param newFile The modified file content
   * @returns Observable of DiffResult
   */
  postDiff(oldFile: string, newFile: string): Observable<DiffResult> {
    const url = `${this.apiUrl}/diff/parse`;
    const body: DiffRequest = {
      old_file: oldFile,
      new_file: newFile,
    };

    return this.http.post<DiffResult>(url, body).pipe(
      catchError((error: HttpErrorResponse) => {
        return this.handleError(error, 'Failed to parse file differences');
      })
    );
  }

  /**
   * Handles HTTP errors and returns an observable error.
   *
   * @param error The HTTP error response
   * @param defaultMessage Default error message
   * @returns Observable that throws an error
   */
  private handleError(error: HttpErrorResponse, defaultMessage: string): Observable<never> {
    let errorMessage = defaultMessage;

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `${defaultMessage}: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `${defaultMessage}: ${error.status} ${error.statusText}`;
      if (error.error && error.error.detail) {
        errorMessage += ` - ${error.error.detail}`;
      }
    }

    return throwError(() => new Error(errorMessage));
  }
}

