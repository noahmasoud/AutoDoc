import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="dashboard-container">
      <h1>Dashboard</h1>
      <p>Placeholder page for Dashboard.</p>
      
      <div class="dashboard-actions" style="margin-top: 24px;">
        <a routerLink="/connections" class="dashboard-button">
          <span>Configure Confluence Connection</span>
          <span style="font-size: 0.9em; opacity: 0.8;">→</span>
        </a>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 24px;
      max-width: 1200px;
      margin: 0 auto;
    }
    
    .dashboard-actions {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }
    
    .dashboard-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background-color: #1976d2;
      color: white;
      text-decoration: none;
      border-radius: 4px;
      font-weight: 500;
      transition: background-color 0.2s;
      border: none;
      cursor: pointer;
    }
    
    .dashboard-button:hover {
      background-color: #1565c0;
    }
    
    .dashboard-button:active {
      background-color: #0d47a1;
    }
  `]
})
export class DashboardComponent {}
