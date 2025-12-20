import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, BehaviorSubject, throwError, timeout, TimeoutError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly API_URL = `${environment.apiBase}/login`;
  private readonly USERINFO_URL = `${environment.apiBase}/login/userinfo`;
  private authStatusSubject = new BehaviorSubject<boolean>(this.isLoggedIn());
  public authStatus$ = this.authStatusSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    this.checkTokenValidity();
  }

  login(username: string, password: string): Observable<LoginResponse> {
    const loginRequest: LoginRequest = { username, password };
    return this.http.post<LoginResponse>(this.API_URL, loginRequest).pipe(
      timeout(10000), // 10 second timeout
      tap(response => {
        if (response.access_token) {
          localStorage.setItem(this.TOKEN_KEY, response.access_token);
          this.authStatusSubject.next(true);
        }
      }),
      catchError((error: HttpErrorResponse | TimeoutError) => {
        console.error('Login error:', error);
        if (error instanceof TimeoutError) {
          return throwError(() => ({
            status: 0,
            error: { detail: 'Request timed out. Please check if the backend server is running.' }
          }));
        }
        return throwError(() => error);
      })
    );
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    this.authStatusSubject.next(false);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    const token = this.getToken();
    return !!token;
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getAuthStatus(): Observable<boolean> {
    return this.authStatus$;
  }

  private checkTokenValidity(): void {
    const token = this.getToken();
    if (!token) {
      this.authStatusSubject.next(false);
      return;
    }
    // Use timeout and catchError to prevent hanging requests
    this.http.get(this.USERINFO_URL).pipe(
      timeout(5000), // 5 second timeout for token validation
      catchError((error: HttpErrorResponse | TimeoutError) => {
        // Token is invalid or request timed out, clear it
        localStorage.removeItem(this.TOKEN_KEY);
        this.authStatusSubject.next(false);
        // Don't log timeout errors as they're expected if backend is down
        if (!(error instanceof TimeoutError)) {
          console.debug('Token validation failed:', error);
        }
        return throwError(() => error);
      })
    ).subscribe({
      next: () => this.authStatusSubject.next(true),
      error: () => {
        // Error already handled in pipe
      }
    });
  }
}
