import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Prompt {
  id: number;
  name: string;
  content: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PromptCreate {
  name: string;
  content: string;
  is_default?: boolean;
  is_active?: boolean;
}

export interface PromptUpdate {
  name?: string;
  content?: string;
  is_active?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class PromptsService {
  private apiUrl = `${environment.apiBase}/v1/prompts`;

  constructor(private http: HttpClient) {}

  // List all prompts
  listPrompts(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(this.apiUrl);
  }

  // Get a single prompt by ID
  getPrompt(id: number): Observable<Prompt> {
    return this.http.get<Prompt>(`${this.apiUrl}/${id}`);
  }

  // Create a new prompt
  createPrompt(prompt: PromptCreate): Observable<Prompt> {
    return this.http.post<Prompt>(this.apiUrl, prompt);
  }

  // Update an existing prompt
  updatePrompt(id: number, prompt: PromptUpdate): Observable<Prompt> {
    return this.http.put<Prompt>(`${this.apiUrl}/${id}`, prompt);
  }

  // Delete a prompt
  deletePrompt(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }
}

