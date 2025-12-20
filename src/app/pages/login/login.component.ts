import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatProgressSpinnerModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  isLoading = false;
  returnUrl = '/dashboard';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private toastService: ToastService
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
    if (this.authService.isLoggedIn()) {
      this.router.navigate([this.returnUrl]);
    }
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;

    const { username, password } = this.loginForm.value;

    this.authService.login(username, password).subscribe({
      next: () => {
        this.toastService.success('Login successful!');
        this.router.navigate([this.returnUrl]);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Login error details:', error);
        let errorMessage = 'Login failed. Please try again.';
        
        // Check for timeout error
        if (error.error?.detail?.includes('timed out') || error.name === 'TimeoutError') {
          errorMessage = 'Request timed out. The backend server may not be running or is taking too long to respond. Please check http://localhost:8000';
        } else if (error.status === 401) {
          errorMessage = 'Invalid username or password. Please try again.';
        } else if (error.status === 400) {
          const detail = error.error?.detail || error.error?.message || JSON.stringify(error.error);
          errorMessage = `Bad Request: ${detail}. Please check your input.`;
          console.error('400 Bad Request details:', error.error);
        } else if (error.status === 0 || error.status === undefined) {
          errorMessage = 'Unable to connect to server. Please ensure the backend is running on http://localhost:8000';
        } else {
          errorMessage = error.error?.detail || error.error?.message || `Login failed (${error.status}). Please try again.`;
        }
        
        this.toastService.error(errorMessage);
      }
    });
  }

  getFieldError(fieldName: string): string {
    const field = this.loginForm.get(fieldName);
    if (field && field.invalid && field.touched) {
      if (field.errors?.['required']) {
        return `${fieldName} is required`;
      }
    }
    return '';
  }
}

