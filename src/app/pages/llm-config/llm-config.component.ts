import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { LLMConfigService, LLMConfig, LLMConfigCreate } from '../../services/llm-config.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-llm-config',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatProgressSpinnerModule],
  templateUrl: './llm-config.component.html',
  styleUrls: ['./llm-config.component.css']
})
export class LLMConfigComponent implements OnInit {
  llmConfigForm: FormGroup;
  isApiKeySaved = false;
  existingConfig: LLMConfig | null = null;
  isLoading = false;
  isSaving = false;
  isTesting = false;

  // Available LLM models
  availableModels = [
    // OpenAI Models
    { value: 'gpt-4o', label: 'OpenAI GPT-4o' },
    { value: 'gpt-4o-mini', label: 'OpenAI GPT-4o Mini' },
    { value: 'gpt-4-turbo', label: 'OpenAI GPT-4 Turbo' },
    { value: 'gpt-4', label: 'OpenAI GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'OpenAI GPT-3.5 Turbo' },
    // Anthropic Claude Models
    { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (2025-05-14)' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (2024-10-22)' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus (2024-02-29)' },
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet (2024-02-29)' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku (2024-03-07)' },
  ];

  constructor(
    private fb: FormBuilder,
    private llmConfigService: LLMConfigService,
    private toastService: ToastService
  ) {
    this.llmConfigForm = this.fb.group({
      model: ['', [Validators.required]],
      api_key: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    this.loadLLMConfig();
  }

  loadLLMConfig(): void {
    this.isLoading = true;
    this.llmConfigService.getLLMConfig().subscribe({
      next: (config) => {
        if (config) {
          this.existingConfig = config;
          this.llmConfigForm.patchValue({
            model: config.model,
            api_key: '••••••••••'
          });
          this.isApiKeySaved = true;
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading LLM configuration:', error);
        this.isLoading = false;
      }
    });
  }

  saveLLMConfig(): void {
    if (this.llmConfigForm.invalid) {
      this.llmConfigForm.markAllAsTouched();
      this.toastService.error('Please fill in all required fields correctly.');
      return;
    }

    const formValue = this.llmConfigForm.value;
    
    // Only send API key if it's not the masked value
    const apiKeyValue = formValue.api_key;
    if (!apiKeyValue || apiKeyValue === '••••••••••') {
      this.toastService.info('Please enter a new API key to update the configuration.');
      return;
    }

    const configData: LLMConfigCreate = {
      model: formValue.model,
      api_key: apiKeyValue
    };

    this.isSaving = true;
    this.llmConfigService.saveLLMConfig(configData).subscribe({
      next: (config) => {
        this.existingConfig = config;
        this.toastService.success('LLM configuration saved successfully.');
        this.isApiKeySaved = true;
        this.llmConfigForm.patchValue({ api_key: '••••••••••' });
        this.isSaving = false;
      },
      error: (error) => {
        console.error('Error saving LLM configuration:', error);
        const errorMsg = error.error?.detail || 'Failed to save LLM configuration. Please try again.';
        this.toastService.error(errorMsg);
        this.isSaving = false;
      }
    });
  }

  testLLMConfig(): void {
    if (this.llmConfigForm.invalid) {
      this.llmConfigForm.markAllAsTouched();
      this.toastService.error('Please fill in all required fields correctly.');
      return;
    }

    const formValue = this.llmConfigForm.value;
    const apiKeyValue = formValue.api_key;
    
    if (!apiKeyValue || apiKeyValue === '••••••••••') {
      this.toastService.error('Please enter an API key to test the configuration.');
      return;
    }

    this.isTesting = true;

    this.llmConfigService.testLLMConfig({
      model: formValue.model,
      api_key: apiKeyValue
    }).subscribe({
      next: (response) => {
        this.isTesting = false;
        if (response.ok) {
          this.toastService.success(response.details);
        } else {
          this.toastService.error(response.details);
          // Clear API key field if invalid
          if (response.details.includes('invalid')) {
            this.llmConfigForm.patchValue({ api_key: '' });
            this.isApiKeySaved = false;
          }
        }
      },
      error: (error) => {
        this.isTesting = false;
        console.error('Error testing LLM configuration:', error);
        const errorMsg = error.error?.detail || 'Failed to test LLM configuration. Please try again.';
        this.toastService.error(errorMsg);
      }
    });
  }

  getControl(name: string) {
    return this.llmConfigForm.get(name);
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
    }
    return '';
  }
}

