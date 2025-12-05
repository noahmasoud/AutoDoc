import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TemplatesService, Template, TemplateCreate } from '../../services/templates.service';

@Component({
  selector: 'app-templates',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './templates.component.html',
  styleUrls: ['./templates.component.css']
})
// execute onInit
export class TemplatesComponent implements OnInit {
  templates: Template[] = [];
  filteredTemplates: Template[] = [];
  searchQuery = '';
  loading = false;
  error: string | null = null;

  // editor state
  showEditor = false;
  editingTemplate: Template | null = null;
  templateForm: TemplateCreate = {
    name: '',
    format: 'Markdown',
    body: '',
    variables: null
  };

  constructor(private templatesService: TemplatesService) { }

  ngOnInit(): void {
    this.loadTemplates();
  }
  getVariableKeys(variables: Record<string, any> | null): string[] {
    return variables ? Object.keys(variables) : [];
  }

  getVariableDescription(varName: string): string {
    const varData = this.templateForm.variables?.[varName];
    if (typeof varData === 'object' && varData !== null && 'description' in varData) {
      return varData.description;
    }
    return 'No description available';
  }
  getVariableExample(varName: string): string | null {
    const varData = this.templateForm.variables?.[varName];
    if (typeof varData === 'object' && varData !== null && 'example' in varData) {
      return varData.example;
    }
    return null;
  }

  insertVariable(varName: string, textarea: HTMLTextAreaElement): void {
    const cursorPos = textarea.selectionStart;
    const textBefore = this.templateForm.body.substring(0, cursorPos);
    const textAfter = this.templateForm.body.substring(cursorPos);

    const variableText = `{{${varName}}}`;
    this.templateForm.body = textBefore + variableText + textAfter;

    // fix cursor position after inserted variable to stay in place
    setTimeout(() => {
      textarea.focus();
      const newPos = cursorPos + variableText.length;
      textarea.setSelectionRange(newPos, newPos);
    }, 0);
  }

  loadTemplates(): void {
    this.loading = true;
    this.error = null;

    this.templatesService.listTemplates().subscribe({
      next: (templates) => {
        this.templates = templates;
        this.filteredTemplates = templates;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load templates';
        this.loading = false;
        console.error('Error loading templates:', err);
      }
    });
  }

  filterTemplates(): void {
    const query = this.searchQuery.toLowerCase();
    this.filteredTemplates = this.templates.filter(t =>
      t.name.toLowerCase().includes(query) ||
      t.format.toLowerCase().includes(query)
    );
  }

  openCreateDialog(): void {
    this.editingTemplate = null;
    this.templateForm = {
      name: '',
      format: 'Markdown',
      body: '',
      variables: null
    };
    this.showEditor = true;
  }

  openEditDialog(template: Template): void {
    this.editingTemplate = template;
    this.templateForm = {
      name: template.name,
      format: template.format,
      body: template.body,
      variables: template.variables
    };
    this.showEditor = true;
  }

  closeEditor(): void {
    this.showEditor = false;
    this.editingTemplate = null;
    this.error = null;
  }

  saveTemplate(): void {
    this.error = null;

    // Validation
    if (!this.templateForm.name.trim()) {
      this.error = 'Template name is required';
      return;
    }
    if (!this.templateForm.body.trim()) {
      this.error = 'Template body is required';
      return;
    }

    this.loading = true;

    if (this.editingTemplate) {
      // update existing template
      this.templatesService.updateTemplate(this.editingTemplate.id, this.templateForm).subscribe({
        next: () => {
          this.loadTemplates();
          this.closeEditor();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to update template';
          this.loading = false;
        }
      });
    } else {
      // create new template
      this.templatesService.createTemplate(this.templateForm).subscribe({
        next: () => {
          this.loadTemplates();
          this.closeEditor();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to create template';
          this.loading = false;
        }
      });
    }
  }

  deleteTemplate(template: Template): void {
    if (!confirm(`Are you sure you want to delete "${template.name}"?`)) {
      return;
    }

    this.loading = true;
    this.templatesService.deleteTemplate(template.id).subscribe({
      next: () => {
        this.loadTemplates();
      },
      error: (err) => {
        this.error = 'Failed to delete template';
        this.loading = false;
        console.error('Error deleting template:', err);
      }
    });
  }
}