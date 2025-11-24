import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ConnectionsService } from '../../services/connections.service';
import { RulesService } from '../../services/rules.service';
import { TemplatesService } from '../../services/templates.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  connectionStatus: 'configured' | 'not-configured' = 'not-configured';
  connectionUrl: string = '';
  rulesCount: number = 0;
  templatesCount: number = 0;
  isLoading = true;

  constructor(
    private connectionsService: ConnectionsService,
    private rulesService: RulesService,
    private templatesService: TemplatesService
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData(): void {
    this.isLoading = true;

    // Load connection
    this.connectionsService.getConnection().subscribe({
      next: (connection) => {
        if (connection) {
          this.connectionStatus = 'configured';
          this.connectionUrl = connection.confluence_base_url;
        } else {
          this.connectionStatus = 'not-configured';
        }
      },
      error: () => {
        this.connectionStatus = 'not-configured';
      }
    });

    // Load rules count
    this.rulesService.listRules().subscribe({
      next: (rules) => {
        this.rulesCount = rules.length;
        this.checkLoadingComplete();
      },
      error: () => {
        this.rulesCount = 0;
        this.checkLoadingComplete();
      }
    });

    // Load templates count
    this.templatesService.listTemplates().subscribe({
      next: (templates) => {
        this.templatesCount = templates.length;
        this.checkLoadingComplete();
      },
      error: () => {
        this.templatesCount = 0;
        this.checkLoadingComplete();
      }
    });
  }

  private checkLoadingComplete(): void {
    // Simple check - all three services have responded
    // In a real app, you might use forkJoin or similar
    this.isLoading = false;
  }
}
