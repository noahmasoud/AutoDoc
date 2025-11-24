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
  private readonly maxDelayMs = 8000;
  private readonly jitterRatio = 0.5;

  intercept(
    req: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    return this.executeWithRetry(req, () => next.handle(req));
  }

  /**
   * Wrapper around HTTP handler execution so we can layer retry behavior
   * incrementally across implementation steps.
   */
  private executeWithRetry(
    request: HttpRequest<unknown>,
    requestFn: () => Observable<HttpEvent<unknown>>,
  ): Observable<HttpEvent<unknown>> {
    return defer(requestFn).pipe(
      retryWhen((errors) =>
        errors.pipe(
          mergeMap((error, attempt) => {
            if (!this.isRetryableError(error) || attempt >= this.maxRetries) {
              this.logFinalFailure(error, request, attempt);
              return throwError(() => error);
            }
            const delayMs = this.getRetryDelay(attempt);
            this.logRetryAttempt(error, request, attempt, delayMs);
            return timer(delayMs);
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
    const exponentialDelay = this.baseDelayMs * 2 ** attempt;
    const cappedDelay = Math.min(exponentialDelay, this.maxDelayMs);
    const jitterRange = cappedDelay * this.jitterRatio;
    const jitter = Math.random() * jitterRange;

    return cappedDelay + jitter;
  }

  private logRetryAttempt(
    error: unknown,
    request: HttpRequest<unknown>,
    attempt: number,
    delayMs: number,
  ): void {
    const retryNumber = attempt + 1;
    const message = [
      `[HTTP Retry] Attempt ${retryNumber}/${this.maxRetries} scheduled`,
      `method=${request.method}`,
      `url=${request.urlWithParams}`,
      `delay=${Math.round(delayMs)}ms`,
      `reason=${this.describeError(error)}`,
    ].join(' | ');

    console.warn(message);
  }

  private logFinalFailure(
    error: unknown,
    request: HttpRequest<unknown>,
    attempt: number,
  ): void {
    const attempts = Math.min(attempt, this.maxRetries) + 1;
    const message = [
      '[HTTP Retry] Giving up after attempts',
      attempts.toString(),
      `method=${request.method}`,
      `url=${request.urlWithParams}`,
      `reason=${this.describeError(error)}`,
    ].join(' | ');

    console.error(message);
  }

  private describeError(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) {
        return 'Network error or timeout';
      }
      return `HTTP ${error.status} ${error.statusText || ''}`.trim();
    }

    if (error instanceof TimeoutError) {
      return 'Request timed out';
    }

    if (error instanceof Error) {
      return error.message;
    }

    return 'Unknown error';
  }
}

