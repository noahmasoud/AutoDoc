import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ConnectionsService, Connection, ConnectionCreate, ConnectionTestRequest } from '../../services/connections.service';

@Component({
  selector: 'app-connections',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './connections.component.html',
  styleUrl: './connections.component.css'
})
export class ConnectionsComponent implements OnInit {
  connectionForm: FormGroup;
  existingConnection: Connection | null = null;
  isLoading = false;
  isTesting = false;
  statusMessage: { type: 'success' | 'error' | 'info'; text: string } | null = null;
  
  // Token management - never display raw token after initial entry
  private originalTokenValue: string | null = null;
  private hasTokenBeenEntered = false;
  isTokenSaved = false; // Public for template access
  
  // Masked token display value
  readonly MASKED_TOKEN = '••••••••••';
  readonly SAVED_TOKEN_DISPLAY = '•••••••••• (saved)';

  constructor(
    private fb: FormBuilder,
    private connectionsService: ConnectionsService
  ) {
    this.connectionForm = this.fb.group({
      confluence_base_url: ['', [Validators.required, Validators.pattern(/^https?:\/\/.+/)]],
      space_key: ['', [Validators.required]],
      api_token: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    this.loadConnection();
  }

  /**
   * Load existing connection from backend.
   * Shows masked token if connection exists.
   */
  loadConnection(): void {
    this.isLoading = true;
    this.connectionsService.getConnection().subscribe({
      next: (connection) => {
        this.existingConnection = connection;
        if (connection) {
          // Populate form with existing data
          this.connectionForm.patchValue({
            confluence_base_url: connection.confluence_base_url,
            space_key: connection.space_key,
            // Never show actual token - use masked display
            api_token: this.SAVED_TOKEN_DISPLAY
          });
          this.isTokenSaved = true;
          // Disable token field until user wants to change it
          this.connectionForm.get('api_token')?.disable();
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load connection:', error);
        this.showStatus('error', 'Failed to load connection settings.');
        this.isLoading = false;
      }
    });
  }

  /**
   * Enable token field when user wants to update it.
   */
  onTokenFieldFocus(): void {
    const tokenControl = this.connectionForm.get('api_token');
    if (tokenControl && this.isTokenSaved) {
      // Clear the masked value when user focuses
      tokenControl.enable();
      tokenControl.setValue('');
      this.isTokenSaved = false;
      this.hasTokenBeenEntered = false;
      this.originalTokenValue = null;
    }
  }

  /**
   * Track token input - store original value but never display it again.
   */
  onTokenInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = input.value;
    
    // Store the actual value if it's a new entry (not the masked display)
    if (value !== this.SAVED_TOKEN_DISPLAY && value !== this.MASKED_TOKEN) {
      this.originalTokenValue = value;
      this.hasTokenBeenEntered = true;
    }
  }

  /**
   * Handle blur event - mask token if it matches the masked pattern or was saved.
   */
  onTokenFieldBlur(): void {
    const tokenControl = this.connectionForm.get('api_token');
    if (tokenControl) {
      const currentValue = tokenControl.value;
      
      // If user cleared the field or it's the masked value, keep it as is
      if (!currentValue || currentValue === this.SAVED_TOKEN_DISPLAY || currentValue === this.MASKED_TOKEN) {
        if (this.isTokenSaved && !this.hasTokenBeenEntered) {
          // Revert to saved display if user didn't enter new value
          tokenControl.setValue(this.SAVED_TOKEN_DISPLAY);
          tokenControl.disable();
        } else if (!this.hasTokenBeenEntered && !currentValue) {
          // Field was cleared, enable for new entry
          tokenControl.enable();
        }
      }
    }
  }

  /**
   * Save connection configuration.
   * Only sends token if user entered a new one.
   */
  saveConnection(): void {
    if (this.connectionForm.invalid) {
      this.markFormGroupTouched(this.connectionForm);
      this.showStatus('error', 'Please fill in all required fields correctly.');
      return;
    }

    const formValue = this.connectionForm.getRawValue();
    
    // Only send token if user entered a new one
    const shouldSendToken = this.hasTokenBeenEntered && this.originalTokenValue;
    
    if (!shouldSendToken && !this.existingConnection) {
      this.showStatus('error', 'Please enter an API token.');
      return;
    }

    this.isLoading = true;
    this.statusMessage = null;

    const connectionData: ConnectionCreate = {
      confluence_base_url: formValue.confluence_base_url.trim(),
      space_key: formValue.space_key.trim(),
      // Only include token if user entered a new one
      api_token: shouldSendToken ? this.originalTokenValue! : ''
    };

    // If not sending a new token, we need to use existing connection's token
    // But since we don't store it in frontend, we'll require user to re-enter
    if (!shouldSendToken && this.existingConnection) {
      this.showStatus('error', 'Please enter a new API token to update the connection.');
      this.isLoading = false;
      return;
    }

    this.connectionsService.saveConnection(connectionData).subscribe({
      next: (connection) => {
        this.existingConnection = connection;
        this.isTokenSaved = true;
        this.hasTokenBeenEntered = false;
        this.originalTokenValue = null;
        
        // Reset token field to show saved state
        const tokenControl = this.connectionForm.get('api_token');
        if (tokenControl) {
          tokenControl.setValue(this.SAVED_TOKEN_DISPLAY);
          tokenControl.disable();
        }
        
        this.showStatus('success', 'Connection saved successfully!');
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to save connection:', error);
        const errorMsg = error.error?.detail || error.error?.message || 'Failed to save connection.';
        this.showStatus('error', errorMsg);
        this.isLoading = false;
      }
    });
  }

  /**
   * Test connection with current form values.
   */
  testConnection(): void {
    if (this.connectionForm.invalid) {
      this.markFormGroupTouched(this.connectionForm);
      this.showStatus('error', 'Please fill in all required fields correctly.');
      return;
    }

    const formValue = this.connectionForm.getRawValue();
    
    // Get token - use original value if entered, otherwise we can't test
    const tokenValue = this.hasTokenBeenEntered && this.originalTokenValue
      ? this.originalTokenValue
      : formValue.api_token;

    // Don't test if token is masked/saved display
    if (tokenValue === this.SAVED_TOKEN_DISPLAY || tokenValue === this.MASKED_TOKEN || !tokenValue) {
      this.showStatus('error', 'Please enter a valid API token to test the connection.');
      return;
    }

    this.isTesting = true;
    this.statusMessage = null;

    const testRequest: ConnectionTestRequest = {
      confluence_base_url: formValue.confluence_base_url.trim(),
      space_key: formValue.space_key.trim(),
      api_token: tokenValue
    };

    this.connectionsService.testConnection(testRequest).subscribe({
      next: (response) => {
        if (response.success) {
          this.showStatus('success', response.message);
        } else {
          this.showStatus('error', response.message);
        }
        this.isTesting = false;
      },
      error: (error) => {
        console.error('Connection test failed:', error);
        const errorMsg = error.error?.message || error.error?.detail || 'Connection test failed.';
        this.showStatus('error', errorMsg);
        this.isTesting = false;
      }
    });
  }

  /**
   * Show status message to user.
   */
  private showStatus(type: 'success' | 'error' | 'info', text: string): void {
    this.statusMessage = { type, text };
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      if (this.statusMessage?.text === text) {
        this.statusMessage = null;
      }
    }, 5000);
  }

  /**
   * Mark all form fields as touched to show validation errors.
   */
  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();
      
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  /**
   * Check if a form field has errors and is touched.
   */
  hasFieldError(fieldName: string): boolean {
    const field = this.connectionForm.get(fieldName);
    return !!(field && field.invalid && field.touched);
  }

  /**
   * Get error message for a form field.
   */
  getFieldError(fieldName: string): string {
    const field = this.connectionForm.get(fieldName);
    if (field && field.errors && field.touched) {
      if (field.errors['required']) {
        return `${this.getFieldLabel(fieldName)} is required.`;
      }
      if (field.errors['pattern']) {
        return `Please enter a valid URL.`;
      }
    }
    return '';
  }

  /**
   * Get display label for form field.
   */
  getFieldLabel(fieldName: string): string {
    const labels: { [key: string]: string } = {
      'confluence_base_url': 'Confluence Base URL',
      'space_key': 'Space Key',
      'api_token': 'API Token'
    };
    return labels[fieldName] || fieldName;
  }
}
