import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ModifiedLine {
  line: number;
  old: string;
  new: string;
}

export interface StructuredDiff {
  added: string[];
  removed: string[];
  modified: ModifiedLine[];
}

export interface Patch {
  id: number;
  run_id: number;
  page_id: string;
  diff_before: string;
  diff_after: string;
  diff_unified: string | null;
  diff_structured: StructuredDiff | null;
  approved_by: string | null;
  applied_at: string | null;
  status: string;
  error_message: Record<string, any> | null;
}

export interface PatchApplyRequest {
  approved_by?: string;
  comment?: string;
}

@Injectable({
  providedIn: 'root',
})
export class PatchesService {
  private apiUrl = `${environment.apiBase}/v1/patches`;

  constructor(private http: HttpClient) {}

  getPatch(patchId: number): Observable<Patch> {
    return this.http.get<Patch>(`${this.apiUrl}/${patchId}`);
  }

  listPatches(runId?: number): Observable<Patch[]> {
    let params = new HttpParams();
    if (runId) {
      params = params.set('run_id', runId.toString());
    }
    return this.http.get<Patch[]>(this.apiUrl, { params });
  }

  applyPatch(patchId: number, request?: PatchApplyRequest): Observable<Patch> {
    let params = new HttpParams();
    if (request?.approved_by) {
      params = params.set('approved_by', request.approved_by);
    }
    return this.http.post<Patch>(`${this.apiUrl}/${patchId}/apply`, null, { params });
  }

  rejectPatch(patchId: number, comment?: string): Observable<void> {
    // TODO: Implement reject endpoint when available
    // For now, we'll use a PATCH or PUT to update status
    return this.http.patch<void>(`${this.apiUrl}/${patchId}/reject`, { comment });
  }
}

