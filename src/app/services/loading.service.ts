import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$: Observable<boolean> = this.loadingSubject.asObservable();

  private loadingCount = 0;

  /**
   * Show loading indicator
   */
  show(): void {
    this.loadingCount++;
    if (this.loadingCount > 0) {
      this.loadingSubject.next(true);
    }
  }

  /**
   * Hide loading indicator
   */
  hide(): void {
    this.loadingCount = Math.max(0, this.loadingCount - 1);
    if (this.loadingCount === 0) {
      this.loadingSubject.next(false);
    }
  }

  /**
   * Reset loading state (useful for error cases)
   */
  reset(): void {
    this.loadingCount = 0;
    this.loadingSubject.next(false);
  }
}

