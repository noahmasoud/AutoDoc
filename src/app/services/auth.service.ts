import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, BehaviorSubject, of, throwError } from 'rxjs';
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
  private readonly API_URL = `${environment.apiBase}/login`;  // POST /api/login
  private readonly USERINFO_URL = `${environment.apiBase}/login/userinfo`;  // GET /api/login/userinfo
  private authStatusSubject = new BehaviorSubject<boolean>(this.isLoggedIn());
  public authStatus$ = this.authStatusSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Check token validity on service initialization
    this.checkTokenValidity();
  }

  /**
   * Login with username and password.
   * Stores JWT token in localStorage on success.
   */
  login(username: string, password: string): Observable<LoginResponse> {
    const loginRequest: LoginRequest = { username, password };
    
    return this.http.post<LoginResponse>(this.API_URL, loginRequest).pipe(
      tap(response => {
        if (response.access_token) {
          localStorage.setItem(this.TOKEN_KEY, response.access_token);
          this.authStatusSubject.next(true);
        }
      }),
      catchError(error => {
        console.error('Login error:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Logout user by removing token and redirecting to login.
   */
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    this.authStatusSubject.next(false);
    this.router.navigate(['/login']);
  }

  /**
   * Check if user is logged in (has valid token).
   */
  isLoggedIn(): boolean {
    const token = this.getToken();
    return !!token; // Token exists check (in production, also verify expiration)
  }

  /**
   * Get JWT token from localStorage.
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Verify token with backend (optional - for checking if token is still valid).
   */
  checkTokenValidity(): void {
    const token = this.getToken();
    if (!token) {
      this.authStatusSubject.next(false);
      return;
    }

    // Verify token with backend (silently fail if backend unavailable)
    this.http.get(this.USERINFO_URL).subscribe({
      next: () => {
        this.authStatusSubject.next(true);
      },
      error: (error) => {
        // Token invalid or backend unavailable, clear it
        // Only clear token on 401 (unauthorized), not on connection errors
        if (error.status === 401 || error.status === 403) {
          localStorage.removeItem(this.TOKEN_KEY);
          this.authStatusSubject.next(false);
        } else {
          // Backend might be down, keep token but mark as unverified
          this.authStatusSubject.next(false);
        }
      }
    });
  }

  /**
   * Get authentication status observable.
   */
  getAuthStatus(): Observable<boolean> {
    return this.authStatus$;
  }
}
