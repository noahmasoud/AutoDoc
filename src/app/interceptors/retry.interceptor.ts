import { Injectable } from '@angular/core';
import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import {
  Observable,
  TimeoutError,
  defer,
  throwError,
  timer,
} from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import { retryWhen } from 'rxjs';

/**
 * Interceptor that wraps HTTP requests to enable retry logic.
 *
 * Subsequent implementation steps will extend this with retry conditions,
 * exponential backoff, and logging.
 */
@Injectable()
export class RetryInterceptor implements HttpInterceptor {
  private readonly maxRetries = 3;
  private readonly baseDelayMs = 500;

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
    return defer(requestFn).pipe(
      retryWhen((errors) =>
        errors.pipe(
          mergeMap((error, attempt) => {
            if (!this.isRetryableError(error) || attempt >= this.maxRetries) {
              return throwError(() => error);
            }
            return timer(this.getRetryDelay(attempt));
          }),
        ),
      ),
    );
  }

  private isRetryableError(error: unknown): boolean {
    if (error instanceof TimeoutError) {
      return true;
    }

    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) {
        return true;
      }
      if (error.status === 429) {
        return true;
      }
      if (error.status >= 500 && error.status < 600) {
        return true;
      }
      if (error.error instanceof TimeoutError) {
        return true;
      }
    }

    return false;
  }

  private getRetryDelay(attempt: number): number {
    return this.baseDelayMs;
  }
}

