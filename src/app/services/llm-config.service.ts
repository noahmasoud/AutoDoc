import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface LLMConfig {
  id?: number;
  model: string;
  last_used_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LLMConfigCreate {
  model: string;
  api_key: string;
}

export interface LLMConfigTestRequest {
  model: string;
  api_key: string;
}

export interface LLMConfigTestResponse {
  ok: boolean;
  details: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class LLMConfigService {
  private apiUrl = `${environment.apiBase}/llm-config`;

  constructor(private http: HttpClient) {}

  /**
   * Get the stored LLM configuration (if any).
   * Never returns the API key value (security requirement).
   */
  getLLMConfig(): Observable<LLMConfig | null> {
    return this.http.get<LLMConfig | null>(this.apiUrl).pipe(
      catchError((error) => {
        if (error.status === 404) {
          return of(null);
        }
        throw error;
      })
    );
  }

  /**
   * Save or update LLM configuration.
   * API key is only sent if provided (not masked value).
   */
  saveLLMConfig(config: LLMConfigCreate): Observable<LLMConfig> {
    return this.http.post<LLMConfig>(this.apiUrl, config);
  }

  /**
   * Test LLM configuration.
   */
  testLLMConfig(config: LLMConfigTestRequest): Observable<LLMConfigTestResponse> {
    return this.http.post<LLMConfigTestResponse>(`${this.apiUrl}/test`, config);
  }
}

