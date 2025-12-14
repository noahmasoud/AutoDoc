import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PromptsService, Prompt, PromptCreate } from '../../services/prompts.service';
import { PromptPreferenceService } from '../../services/prompt-preference.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-prompts',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './prompts.component.html',
  styleUrls: ['./prompts.component.css']
})
export class PromptsComponent implements OnInit {
  prompts: Prompt[] = [];
  filteredPrompts: Prompt[] = [];
  searchQuery = '';
  loading = false;
  error: string | null = null;
  selectedPromptId: number | null = null;

  // Editor state
  showEditor = false;
  editingPrompt: Prompt | null = null;
  promptForm: PromptCreate = {
    name: '',
    content: '',
    is_active: true
  };

  // Viewer state for default prompts
  showViewer = false;
  viewingPrompt: Prompt | null = null;

  constructor(
    private promptsService: PromptsService,
    private promptPreferenceService: PromptPreferenceService,
    private toastService: ToastService
  ) { }

  ngOnInit(): void {
    this.loadPrompts();
    this.selectedPromptId = this.promptPreferenceService.getSelectedPromptId();
  }

  loadPrompts(): void {
    this.loading = true;
    this.error = null;

    this.promptsService.listPrompts().subscribe({
      next: (prompts) => {
        this.prompts = prompts;
        this.filteredPrompts = prompts;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load prompts';
        this.loading = false;
        console.error('Error loading prompts:', err);
      }
    });
  }

  filterPrompts(): void {
    const query = this.searchQuery.toLowerCase();
    this.filteredPrompts = this.prompts.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.content.toLowerCase().includes(query)
    );
  }

  openCreateDialog(): void {
    // Check if we can create more custom prompts (max 10)
    const customPromptCount = this.prompts.filter(p => !p.is_default).length;
    if (customPromptCount >= 10) {
      this.error = 'Maximum of 10 custom prompts allowed. Please delete an existing custom prompt first.';
      return;
    }

    this.editingPrompt = null;
    this.promptForm = {
      name: '',
      content: '',
      is_active: true
    };
    this.showEditor = true;
  }

  openEditDialog(prompt: Prompt): void {
    if (prompt.is_default) {
      this.error = 'Cannot edit default prompts. Only custom prompts can be edited.';
      return;
    }
    this.editingPrompt = prompt;
    this.promptForm = {
      name: prompt.name,
      content: prompt.content,
      is_active: prompt.is_active
    };
    this.showEditor = true;
  }

  closeEditor(): void {
    this.showEditor = false;
    this.editingPrompt = null;
    this.error = null;
  }

  savePrompt(): void {
    this.error = null;

    // Validation
    if (!this.promptForm.name.trim()) {
      this.error = 'Prompt name is required';
      return;
    }
    if (!this.promptForm.content.trim()) {
      this.error = 'Prompt content is required';
      return;
    }

    this.loading = true;

    if (this.editingPrompt) {
      // Update existing prompt
      this.promptsService.updatePrompt(this.editingPrompt.id, this.promptForm).subscribe({
        next: () => {
          this.loadPrompts();
          this.closeEditor();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to update prompt';
          this.loading = false;
        }
      });
    } else {
      // Create new prompt
      this.promptsService.createPrompt(this.promptForm).subscribe({
        next: () => {
          this.loadPrompts();
          this.closeEditor();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to create prompt';
          this.loading = false;
        }
      });
    }
  }

  deletePrompt(prompt: Prompt): void {
    if (prompt.is_default) {
      this.error = 'Cannot delete default prompts. Only custom prompts can be deleted.';
      return;
    }

    if (!confirm(`Are you sure you want to delete "${prompt.name}"?`)) {
      return;
    }

    this.loading = true;
    this.promptsService.deletePrompt(prompt.id).subscribe({
      next: () => {
        this.loadPrompts();
      },
      error: (err) => {
        this.error = 'Failed to delete prompt';
        this.loading = false;
        console.error('Error deleting prompt:', err);
      }
    });
  }

  toggleActive(prompt: Prompt): void {
    if (prompt.is_default) {
      // For default prompts, only allow toggling is_active
      this.promptsService.updatePrompt(prompt.id, { is_active: !prompt.is_active }).subscribe({
        next: () => {
          this.loadPrompts();
        },
        error: (err) => {
          this.error = 'Failed to update prompt status';
          console.error('Error updating prompt:', err);
        }
      });
    }
  }

  getPlaceholderInfo(): string {
    return 'Available placeholders: {repo}, {branch}, {commit_sha}, {patches_count}, {patches_text}';
  }

  selectPrompt(prompt: Prompt): void {
    if (!prompt.is_active) {
      this.error = 'Cannot select an inactive prompt. Please activate it first.';
      return;
    }
    this.promptPreferenceService.setSelectedPromptId(prompt.id);
    this.selectedPromptId = prompt.id;
    this.toastService.success(`"${prompt.name}" is now your selected prompt for LLM summaries`);
  }

  isPromptSelected(prompt: Prompt): boolean {
    return this.selectedPromptId === prompt.id;
  }

  clearSelection(): void {
    this.promptPreferenceService.clearSelection();
    this.selectedPromptId = null;
    this.toastService.info('Default prompt will be used for LLM summaries');
  }

  viewFullPrompt(prompt: Prompt): void {
    if (prompt.is_default) {
      this.viewingPrompt = prompt;
      this.showViewer = true;
    }
  }

  closeViewer(): void {
    this.showViewer = false;
    this.viewingPrompt = null;
  }
}

