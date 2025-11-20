import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface Connection {
  id?: number;
  confluence_base_url: string;
  space_key: string;
  last_used_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ConnectionCreate {
  confluence_base_url: string;
  space_key: string;
  api_token: string;
}

export interface ConnectionTestRequest {
  confluence_base_url: string;
  space_key: string;
  api_token: string;
}

export interface ConnectionTestResponse {
  ok: boolean;
  details: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class ConnectionsService {
  private apiUrl = `${environment.apiBase}/connections`;

  constructor(private http: HttpClient) {}

  /**
   * Get the stored connection (if any).
   * Never returns the token value (security requirement).
   */
  getConnection(): Observable<Connection | null> {
    return this.http.get<Connection | null>(this.apiUrl).pipe(
      catchError((error) => {
        if (error.status === 404) {
          return of(null);
        }
        throw error;
      })
    );
  }

  /**
   * Save or update a connection.
   * Token is only sent if provided (not masked value).
   */
  saveConnection(connection: ConnectionCreate): Observable<Connection> {
    return this.http.post<Connection>(this.apiUrl, connection);
  }

  /**
   * Test a Confluence connection.
   * Makes a harmless API call to validate credentials.
   */
  testConnection(connection: ConnectionTestRequest): Observable<ConnectionTestResponse> {
    return this.http.post<ConnectionTestResponse>(`${this.apiUrl}/test`, connection);
  }
}

