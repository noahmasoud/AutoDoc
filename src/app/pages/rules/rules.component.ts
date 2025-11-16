import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-rules',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-container">
      <h2>Rules</h2>
      <p>Welcome to AutoDoc's Rules page!</p>
      <p>This page will contain configuration rules for documentation patterns.</p>
    </div>
  `,
  styles: [`
    .page-container {
      padding: 24px;
      max-width: 1200px;
      margin: 0 auto;
    }

    h2 {
      font-size: 28px;
      font-weight: 600;
      color: #1a1a1a;
      margin: 0 0 16px 0;
    }

    p {
      color: #666;
      line-height: 1.6;
      margin: 8px 0;
    }
  `]
})
export class RulesComponent {}
