import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RulesService, Rule, RuleRequest } from '../../services/rules.service';
import { TemplatesService, TemplateSummary } from '../../services/templates.service';

@Component({
  selector: 'app-rules',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
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
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private rulesService: RulesService,
    private templatesService: TemplatesService
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
    this.rulesService.listRules().subscribe({
      next: (rules) => {
        this.rules = rules;
      },
      error: (error) => {
        console.error('Error loading rules:', error);
        this.errorMessage = 'Failed to load rules';
      }
    });
  }

  loadTemplates(): void {
    this.templatesService.listTemplates().subscribe({
      next: (templates) => {
        this.templates = templates;
      },
      error: (error) => {
        console.error('Error loading templates:', error);
      }
    });
  }

  startCreate(): void {
    this.editingRule = null;
    this.isCreating = true;
    this.ruleForm.reset({ auto_approve: false, template_id: null });
    this.clearMessages();
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
    this.clearMessages();
  }

  cancelEdit(): void {
    this.editingRule = null;
    this.isCreating = false;
    this.ruleForm.reset({ auto_approve: false, template_id: null });
    this.clearMessages();
  }

  saveRule(): void {
    if (this.ruleForm.invalid) {
      this.ruleForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.clearMessages();

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
        this.successMessage = this.editingRule ? 'Rule updated successfully' : 'Rule created successfully';
        this.loadRules();
        this.editingRule = null;
        this.isCreating = false;
        this.ruleForm.reset({ auto_approve: false, template_id: null });
        this.isSubmitting = false;
      },
      error: (error) => {
        console.error('Error saving rule:', error);
        this.errorMessage = error.error?.detail || 'Failed to save rule';
        this.isSubmitting = false;
      }
    });
  }

  deleteRule(rule: Rule): void {
    if (!confirm(`Are you sure you want to delete rule "${rule.name}"?`)) {
      return;
    }

    this.rulesService.deleteRule(rule.id).subscribe({
      next: () => {
        this.successMessage = 'Rule deleted successfully';
        this.loadRules();
      },
      error: (error) => {
        console.error('Error deleting rule:', error);
        this.errorMessage = 'Failed to delete rule';
      }
    });
  }

  clearMessages(): void {
    this.errorMessage = null;
    this.successMessage = null;
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
}
