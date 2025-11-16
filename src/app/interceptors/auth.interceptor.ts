import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * HTTP Interceptor that:
 * 1. Attaches JWT token from localStorage to all outgoing requests
 * 2. Handles 401 Unauthorized responses by logging out and redirecting to login
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  // Get token from localStorage
  const token = authService.getToken();
  
  // Clone request and add Authorization header if token exists
  let authReq = req;
  if (token) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }
  
  // Handle response
  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // If 401 Unauthorized, clear token and redirect to login
      // BUT: Don't logout on login endpoint (401 means wrong credentials)
      const isLoginEndpoint = req.url.includes('/login');
      if (error.status === 401 && !isLoginEndpoint) {
        authService.logout();
      }
      return throwError(() => error);
    })
  );
};

