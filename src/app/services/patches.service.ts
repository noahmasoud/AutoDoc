import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Patch {
  id: number;
  run_id: number;
  page_id: string;
  diff_before: string;
  diff_after: string;
  approved_by: string | null;
  applied_at: string | null;
  status: string;
  error_message: Record<string, any> | null;
}

@Injectable({
  providedIn: 'root',
})
export class PatchesService {
  private apiUrl = `${environment.apiBase}/patches`;

  constructor(private http: HttpClient) {}

  listPatches(runId?: number): Observable<Patch[]> {
    const url = runId ? `${this.apiUrl}?run_id=${runId}` : this.apiUrl;
    return this.http.get<Patch[]>(url);
  }

  getPatch(patchId: number): Observable<Patch> {
    return this.http.get<Patch>(`${this.apiUrl}/${patchId}`);
  }

  applyPatch(patchId: number, approvedBy?: string): Observable<Patch> {
    const url = `${this.apiUrl}/${patchId}/apply`;
    const params: any = {};
    if (approvedBy) {
      params.approved_by = approvedBy;
    }
    return this.http.post<Patch>(url, null, { params });
  }
}

