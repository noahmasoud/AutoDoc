import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Rule {
  id: number;
  name: string;
  selector: string;
  space_key: string;
  page_id: string;
  template_id: number | null;
  prompt_id: number | null;
  auto_approve: boolean;
  update_strategy: 'replace' | 'append' | 'modify_section';
}

export type RuleRequest = Omit<Rule, 'id'>;

@Injectable({
  providedIn: 'root',
})
export class RulesService {
  private apiUrl = `${environment.apiBase}/v1/rules`;

  constructor(private http: HttpClient) {}

  listRules(): Observable<Rule[]> {
    return this.http.get<Rule[]>(this.apiUrl);
  }

  createRule(rule: RuleRequest): Observable<Rule> {
    return this.http.post<Rule>(this.apiUrl, rule);
  }

  updateRule(ruleId: number, payload: Partial<RuleRequest>): Observable<Rule> {
    return this.http.put<Rule>(`${this.apiUrl}/${ruleId}`, payload);
  }

  deleteRule(ruleId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${ruleId}`);
  }
}

