import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { RulesService, Rule, RuleRequest } from '../../services/rules.service';
import { TemplatesService, TemplateSummary } from '../../services/templates.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-rules',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatProgressSpinnerModule],
  templateUrl: './rules.component.html',
  styleUrls: ['./rules.component.css']
})
export class RulesComponent implements OnInit {
  rules: Rule[] = [];
  templates: TemplateSummary[] = [];
  ruleForm: FormGroup;
  editingRule: Rule | null = null;
  isCreating = false;
  isSubmitting = false;
  isLoading = false;
  isDeleting: { [key: number]: boolean } = {};

  constructor(
    private fb: FormBuilder,
    private rulesService: RulesService,
    private templatesService: TemplatesService,
    private toastService: ToastService
  ) {
    this.ruleForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(1)]],
      selector: ['', [Validators.required]],
      space_key: ['', [Validators.required]],
      page_id: ['', [Validators.required]],
      template_id: [null],
      auto_approve: [false]
    });
  }

  ngOnInit(): void {
    this.loadRules();
    this.loadTemplates();
  }

  loadRules(): void {
    this.isLoading = true;
    this.rulesService.listRules().subscribe({
      next: (rules) => {
        this.rules = rules;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading rules:', error);
        this.toastService.error('Failed to load rules. Please try again.');
        this.isLoading = false;
      }
    });
  }

  loadTemplates(): void {
    this.templatesService.listTemplates().pipe(
      catchError((error) => {
        console.error('Error loading templates:', error);
        return of([]);
      })
    ).subscribe({
      next: (templates) => {
        this.templates = templates;
      }
    });
  }

  startCreate(): void {
    this.editingRule = null;
    this.isCreating = true;
    this.ruleForm.reset({ auto_approve: false, template_id: null });
  }

  startEdit(rule: Rule): void {
    this.editingRule = rule;
    this.isCreating = false;
    this.ruleForm.patchValue({
      name: rule.name,
      selector: rule.selector,
      space_key: rule.space_key,
      page_id: rule.page_id,
      template_id: rule.template_id,
      auto_approve: rule.auto_approve
    });
  }

  cancelEdit(): void {
    this.editingRule = null;
    this.isCreating = false;
    this.ruleForm.reset({ auto_approve: false, template_id: null });
  }

  saveRule(): void {
    if (this.ruleForm.invalid) {
      this.ruleForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;

    const formValue = this.ruleForm.value;
    const ruleData: RuleRequest = {
      name: formValue.name,
      selector: formValue.selector,
      space_key: formValue.space_key,
      page_id: formValue.page_id,
      template_id: formValue.template_id || null,
      auto_approve: formValue.auto_approve || false
    };

    const operation = this.editingRule
      ? this.rulesService.updateRule(this.editingRule.id, ruleData)
      : this.rulesService.createRule(ruleData);

    operation.subscribe({
      next: () => {
        const message = this.editingRule ? 'Rule updated successfully' : 'Rule created successfully';
        this.toastService.success(message);
        this.loadRules();
        this.editingRule = null;
        this.isCreating = false;
        this.ruleForm.reset({ auto_approve: false, template_id: null });
        this.isSubmitting = false;
      },
      error: (error) => {
        console.error('Error saving rule:', error);
        const errorMsg = error.error?.detail || 'Failed to save rule';
        this.toastService.error(errorMsg);
        this.isSubmitting = false;
      }
    });
  }

  deleteRule(rule: Rule): void {
    if (!confirm(`Are you sure you want to delete rule "${rule.name}"?`)) {
      return;
    }

    this.isDeleting[rule.id] = true;

    this.rulesService.deleteRule(rule.id).subscribe({
      next: () => {
        this.toastService.success('Rule deleted successfully');
        this.isDeleting[rule.id] = false;
        this.loadRules();
      },
      error: (error) => {
        console.error('Error deleting rule:', error);
        this.toastService.error('Failed to delete rule');
        this.isDeleting[rule.id] = false;
      }
    });
  }

  getFieldError(fieldName: string): string {
    const field = this.ruleForm.get(fieldName);
    if (field && field.invalid && field.touched) {
      if (field.errors?.['required']) {
        return `${fieldName} is required`;
      }
      if (field.errors?.['minlength']) {
        return `${fieldName} must be at least ${field.errors['minlength'].requiredLength} characters`;
      }
    }
    return '';
  }

  trackByRuleId(index: number, rule: Rule): number {
    return rule.id;
  }
}
