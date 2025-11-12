import { Injectable } from '@angular/core';
import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import { Observable, defer } from 'rxjs';

/**
 * Interceptor that wraps HTTP requests to enable retry logic.
 *
 * Subsequent implementation steps will extend this with retry conditions,
 * exponential backoff, and logging.
 */
@Injectable()
export class RetryInterceptor implements HttpInterceptor {
  intercept(
    req: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    return this.executeWithRetry(() => next.handle(req));
  }

  /**
   * Wrapper around HTTP handler execution so we can layer retry behavior
   * incrementally across implementation steps.
   */
  private executeWithRetry(
    requestFn: () => Observable<HttpEvent<unknown>>,
  ): Observable<HttpEvent<unknown>> {
    return defer(requestFn);
  }
}

