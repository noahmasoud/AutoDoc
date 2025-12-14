import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PromptPreferenceService {
  private readonly SELECTED_PROMPT_KEY = 'selected_prompt_id';
  private selectedPromptIdSubject = new BehaviorSubject<number | null>(this.getSelectedPromptId());
  public selectedPromptId$ = this.selectedPromptIdSubject.asObservable();

  /**
   * Get the currently selected prompt ID from localStorage
   */
  getSelectedPromptId(): number | null {
    const stored = localStorage.getItem(this.SELECTED_PROMPT_KEY);
    if (stored === null || stored === 'null') {
      return null;
    }
    const id = parseInt(stored, 10);
    return isNaN(id) ? null : id;
  }

  /**
   * Set the selected prompt ID and save to localStorage
   */
  setSelectedPromptId(promptId: number | null): void {
    if (promptId === null) {
      localStorage.removeItem(this.SELECTED_PROMPT_KEY);
    } else {
      localStorage.setItem(this.SELECTED_PROMPT_KEY, promptId.toString());
    }
    this.selectedPromptIdSubject.next(promptId);
  }

  /**
   * Clear the selected prompt preference
   */
  clearSelection(): void {
    this.setSelectedPromptId(null);
  }
}

