import { Component } from '@angular/core';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-nav',
  template: `
    <nav>
      <div style="display:flex;gap:16px;align-items:center;">
        <div class="brand">AutoDoc</div>
        <a routerLink="/dashboard">Dashboard</a>
        <a routerLink="/connections">Connections</a>
        <a routerLink="/rules">Rules</a>
        <a routerLink="/templates">Templates</a>
        <a routerLink="/code-testing">Code Testing</a>
        <a routerLink="/auto-doc">Auto-Doc</a>
        <a routerLink="/confluence">Confluence</a>
        <a routerLink="/settings">Settings</a>
      </div>
      <div>
        <button *ngIf="!auth.isAuthenticated()" (click)="auth.loginPlaceholder()">Sign in</button>
        <button *ngIf="auth.isAuthenticated()" (click)="auth.logout()">Sign out</button>
      </div>
    </nav>
  `
})
export class NavComponent {
  constructor(public auth: AuthService) {}
}
