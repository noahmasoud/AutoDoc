import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarConfig, MatSnackBarRef, TextOnlySnackBar } from '@angular/material/snack-bar';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastConfig {
  duration?: number;
  action?: string;
  horizontalPosition?: 'start' | 'center' | 'end' | 'left' | 'right';
  verticalPosition?: 'top' | 'bottom';
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private readonly defaultDuration = 5000; // 5 seconds
  private readonly defaultHorizontalPosition: 'start' | 'center' | 'end' | 'left' | 'right' = 'end';
  private readonly defaultVerticalPosition: 'top' | 'bottom' = 'top';

  constructor(private snackBar: MatSnackBar) {}

  /**
   * Show a success toast notification
   */
  success(message: string, config?: ToastConfig): MatSnackBarRef<TextOnlySnackBar> {
    return this.show(message, 'success', config);
  }

  /**
   * Show an error toast notification
   */
  error(message: string, config?: ToastConfig): MatSnackBarRef<TextOnlySnackBar> {
    return this.show(message, 'error', config);
  }

  /**
   * Show an info toast notification
   */
  info(message: string, config?: ToastConfig): MatSnackBarRef<TextOnlySnackBar> {
    return this.show(message, 'info', config);
  }

  /**
   * Show a warning toast notification
   */
  warning(message: string, config?: ToastConfig): MatSnackBarRef<TextOnlySnackBar> {
    return this.show(message, 'warning', config);
  }

  /**
   * Show a toast notification with custom type
   */
  show(
    message: string,
    type: ToastType = 'info',
    config?: ToastConfig
  ): MatSnackBarRef<TextOnlySnackBar> {
    const snackBarConfig: MatSnackBarConfig = {
      duration: config?.duration ?? this.defaultDuration,
      horizontalPosition: config?.horizontalPosition ?? this.defaultHorizontalPosition,
      verticalPosition: config?.verticalPosition ?? this.defaultVerticalPosition,
      panelClass: [`toast-${type}`],
      data: { message, type }
    };

    return this.snackBar.open(
      message,
      config?.action ?? 'Close',
      snackBarConfig
    );
  }
}

