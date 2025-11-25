import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ConnectionsService, Connection, ConnectionCreate } from '../../services/connections.service';

@Component({
  selector: 'app-connections',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatProgressSpinnerModule],
  templateUrl: './connections.component.html',
  styleUrls: ['./connections.component.css']
})
export class ConnectionsComponent implements OnInit {
  connectionForm: FormGroup;
  isTokenSaved = false;
  existingConnection: Connection | null = null;
  statusMessage: { type: 'success' | 'error' | 'info'; text: string } | null = null;
  isLoading = false;
  isSaving = false;
  isTesting = false;

  constructor(
    private fb: FormBuilder,
    private connectionsService: ConnectionsService
  ) {
    this.connectionForm = this.fb.group({
      confluence_base_url: ['', [Validators.required, Validators.pattern(/^https?:\/\/.+/i)]],
      space_key: ['', [Validators.required]],
      api_token: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    this.loadConnection();
  }

  loadConnection(): void {
    this.isLoading = true;
    this.connectionsService.getConnection().subscribe({
      next: (connection) => {
        if (connection) {
          this.existingConnection = connection;
          this.connectionForm.patchValue({
            confluence_base_url: connection.confluence_base_url,
            space_key: connection.space_key,
            api_token: '••••••••••'
          });
          this.isTokenSaved = true;
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading connection:', error);
        this.isLoading = false;
      }
    });
  }

  saveConnection(): void {
    if (this.connectionForm.invalid) {
      this.connectionForm.markAllAsTouched();
      this.statusMessage = {
        type: 'error',
        text: 'Please fill in all required fields correctly.'
      };
      return;
    }

    const formValue = this.connectionForm.value;
    
    // Only send token if it's not the masked value
    const tokenValue = formValue.api_token;
    if (!tokenValue || tokenValue === '••••••••••') {
      this.statusMessage = {
        type: 'info',
        text: 'Please enter a new token to update the connection.'
      };
      return;
    }

    const connectionData: ConnectionCreate = {
      confluence_base_url: formValue.confluence_base_url,
      space_key: formValue.space_key,
      api_token: tokenValue
    };

    this.isSaving = true;
    this.connectionsService.saveConnection(connectionData).subscribe({
      next: (connection) => {
        this.existingConnection = connection;
        this.statusMessage = {
          type: 'success',
          text: 'Connection saved successfully.'
        };
        this.isTokenSaved = true;
        this.connectionForm.patchValue({ api_token: '••••••••••' });
        this.isSaving = false;
      },
      error: (error) => {
        console.error('Error saving connection:', error);
        this.statusMessage = {
          type: 'error',
          text: error.error?.detail || 'Failed to save connection. Please try again.'
        };
        this.isSaving = false;
      }
    });
  }

  testConnection(): void {
    if (this.connectionForm.invalid) {
      this.connectionForm.markAllAsTouched();
      this.statusMessage = {
        type: 'error',
        text: 'Please fill in all required fields correctly.'
      };
      return;
    }

    this.isTesting = true;
    this.statusMessage = null;

    // Test connection functionality will be implemented in Prompt 3
    // For now, simulate a test
    setTimeout(() => {
      this.isTesting = false;
      this.statusMessage = {
        type: 'info',
        text: 'Test connection functionality will be implemented.'
      };
    }, 1000);
  }

  getControl(name: string) {
    return this.connectionForm.get(name);
  }

  hasError(controlName: string): boolean {
    const control = this.getControl(controlName);
    return !!(control && control.invalid && control.touched);
  }

  getErrorMessage(controlName: string): string {
    const control = this.getControl(controlName);
    if (control && control.errors) {
      if (control.errors['required']) {
        return `${controlName} is required`;
      }
      if (control.errors['pattern']) {
        return 'Please enter a valid URL (http:// or https://)';
      }
    }
    return '';
  }
}
