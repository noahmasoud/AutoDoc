import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface TemplateSummary {
  id: number;
  name: string;
  format: string;
  body: string;
  variables?: Record<string, unknown> | null;
}

@Injectable({
  providedIn: 'root',
})
export class TemplatesService {
  private apiUrl = `${environment.apiBase}/v1/templates`;

  constructor(private http: HttpClient) {}

  listTemplates(): Observable<TemplateSummary[]> {
    return this.http.get<TemplateSummary[]>(this.apiUrl);
  }
}

