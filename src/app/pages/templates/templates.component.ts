import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TemplatesService, Template, TemplateCreate } from '../../services/templates.service';

interface TemplateVariable {
  name: string;
  description: string;
  example?: string;
}

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

  // Available template variables
  readonly availableVariables: TemplateVariable[] = [
    { name: 'run.id', description: 'The run ID', example: '123' },
    { name: 'run.repo', description: 'Repository name', example: 'my-repo' },
    { name: 'run.branch', description: 'Git branch name', example: 'main' },
    { name: 'run.commit_sha', description: 'Git commit SHA', example: 'abc123def' },
    { name: 'run.status', description: 'Run status', example: 'completed' },
    { name: 'file_path', description: 'Path to the file with changes', example: 'src/api.py' },
    { name: 'files', description: 'List of files with changes (formatted as markdown list)', example: '- src/api.py\n- src/utils.py' },
    { name: 'rule_name', description: 'Name of the matching rule', example: 'API Documentation Rule' },
    { name: 'rule.name', description: 'Name of the matching rule', example: 'API Documentation Rule' },
    { name: 'rule.page_id', description: 'Confluence page ID for this rule', example: '123456' },
    { name: 'rule.space_key', description: 'Confluence space key', example: 'DOCS' },
    { name: 'page_id', description: 'Confluence page ID', example: '123456' },
    { name: 'space_key', description: 'Confluence space key', example: 'DOCS' },
    { name: 'change_count', description: 'Total number of changes', example: '5' },
    { name: 'added_count', description: 'Number of added changes', example: '2' },
    { name: 'modified_count', description: 'Number of modified changes', example: '2' },
    { name: 'removed_count', description: 'Number of removed changes', example: '1' },
    { name: 'added_symbols', description: 'Comma-separated list of added symbol names', example: 'process_request, handle_error' },
    { name: 'modified_symbols', description: 'Comma-separated list of modified symbol names', example: 'validate_input' },
    { name: 'removed_symbols', description: 'Comma-separated list of removed symbol names', example: 'old_function' },
    { name: 'changes.all', description: 'Formatted string representation of all changes', example: '- process_request (added)\n- handle_error (modified)' },
    { name: 'symbol', description: 'Symbol name from the first change (if single change)', example: 'process_request' },
    { name: 'change_type', description: 'Change type from the first change (if single change)', example: 'added' },
    { name: 'signature', description: 'Function signature (if single change and available)', example: 'def process_request(data: dict) -> str' },
    { name: 'signature_before', description: 'Function signature before change (if available)', example: 'def process_request(data)' },
    { name: 'signature_after', description: 'Function signature after change (if available)', example: 'def process_request(data: dict) -> str' },
  ];

  constructor(private templatesService: TemplatesService) { }

  ngOnInit(): void {
    this.loadTemplates();
  }
  getVariableKeys(variables: Record<string, any> | null): string[] {
    return variables ? Object.keys(variables) : [];
  }

  getVariableDescription(varName: string): string {
    // First check the available variables list
    const varInfo = this.availableVariables.find(v => v.name === varName);
    if (varInfo) {
      return varInfo.description;
    }
    // Fallback to template variables if available
    const varData = this.templateForm.variables?.[varName];
    if (typeof varData === 'object' && varData !== null && 'description' in varData) {
      return varData.description;
    }
    return 'No description available';
  }

  getVariableExample(varName: string): string | null {
    // First check the available variables list
    const varInfo = this.availableVariables.find(v => v.name === varName);
    if (varInfo && varInfo.example) {
      return varInfo.example;
    }
    // Fallback to template variables if available
    const varData = this.templateForm.variables?.[varName];
    if (typeof varData === 'object' && varData !== null && 'example' in varData) {
      return varData.example;
    }
    return null;
  }

  insertVariable(varName: string, textarea?: HTMLTextAreaElement): void {
    const cursorPos = textarea?.selectionStart || this.templateForm.body.length;
    const textBefore = this.templateForm.body.substring(0, cursorPos);
    const textAfter = this.templateForm.body.substring(cursorPos);

    const variableText = `{{${varName}}}`;
    this.templateForm.body = textBefore + variableText + textAfter;

    // update cursor position if textarea is provided
    if (textarea) {
      setTimeout(() => {
        const newPos = cursorPos + variableText.length;
        textarea.selectionStart = newPos;
        textarea.selectionEnd = newPos;
        textarea.focus();
      }, 0);
    }
  }

  // Drag and drop handlers
  onDragStart(event: DragEvent, variableName: string): void {
    if (event.dataTransfer) {
      event.dataTransfer.setData('text/plain', variableName);
      event.dataTransfer.effectAllowed = 'copy';
      if (event.target instanceof HTMLElement) {
        const item = event.target.closest('.variable-item');
        if (item instanceof HTMLElement) {
          item.style.opacity = '0.5';
        }
      }
    }
  }

  onDragEnd(event: DragEvent): void {
    if (event.target instanceof HTMLElement) {
      const item = event.target.closest('.variable-item');
      if (item instanceof HTMLElement) {
        item.style.opacity = '1';
      }
    }
  }

  onDragOver(event: DragEvent, textarea?: HTMLTextAreaElement): void {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'copy';
    }
    if (textarea) {
      textarea.classList.add('drag-over');
    }
  }

  onDragLeave(event: DragEvent, textarea?: HTMLTextAreaElement): void {
    if (textarea) {
      textarea.classList.remove('drag-over');
    }
  }

  onDrop(event: DragEvent, textarea: HTMLTextAreaElement): void {
    event.preventDefault();
    textarea.classList.remove('drag-over');
    
    const variableName = event.dataTransfer?.getData('text/plain');
    if (variableName && textarea) {
      // Focus the textarea first to get accurate cursor position
      textarea.focus();
      
      // Use current cursor position or end of text
      const cursorPos = textarea.selectionStart || this.templateForm.body.length;
      const textBefore = this.templateForm.body.substring(0, cursorPos);
      const textAfter = this.templateForm.body.substring(cursorPos);
      
      const variableText = `{{${variableName}}}`;
      this.templateForm.body = textBefore + variableText + textAfter;
      
      // Update cursor position after insertion
      setTimeout(() => {
        const newPos = cursorPos + variableText.length;
        textarea.selectionStart = newPos;
        textarea.selectionEnd = newPos;
        textarea.focus();
      }, 0);
    }
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