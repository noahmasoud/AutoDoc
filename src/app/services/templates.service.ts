import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Template {
  id: number;
  name: string;
  format: string;
  body: string;
  variables?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}
export interface TemplateCreate {
  name: string;
  format: string;
  body: string;
  variables?: Record<string, any> | null;
}
export interface TemplateUpdate {
  name?: string;
  format?: string;
  body: string;
  variables?: Record<string, any> | null;

}
export interface TemplatePreviewRequest {
  template_body: string;
  variables: Record<string, any>;
  format?: string;

}
export interface TemplatePreviewResponse {
  rendered: string;
}
@Injectable({
  providedIn: 'root',
})

export class TemplatesService {
  private apiUrl = `${environment.apiBase}/v1/templates`;
  constructor(private http: HttpClient) { }

  // list all
  listTemplates(): Observable<Template[]> {
    return this.http.get<Template[]>(this.apiUrl);
  }
  // get a singular new 
  getTemplate(id: number): Observable<Template> {
    return this.http.get<Template>(`${this.apiUrl}/${id}`);
  }
  // create new
  createTemplate(template: TemplateCreate): Observable<Template> {
    return this.http.post<Template>(this.apiUrl, template)
  }
  // update existing
  updateTemplate(id: number, template: TemplateUpdate): Observable<Template> {
    return this.http.put<Template>(`${this.apiUrl}/${id}`, template);
  }
  // delete exsisting
  deleteTemplate(id: number): Observable<void> {
    return this.http.delete<any>(`${this.apiUrl}/${id}`);
  }
  // preview existing
  previewTemplate(request: TemplatePreviewRequest): Observable<TemplatePreviewResponse> {
    return this.http.post<TemplatePreviewResponse>(`${this.apiUrl}/preview`, request);
  }
}

