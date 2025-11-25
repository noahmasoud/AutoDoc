import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ConnectionsService } from '../../services/connections.service';
import { RulesService } from '../../services/rules.service';
import { TemplatesService } from '../../services/templates.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, MatProgressSpinnerModule],
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

    // Load all data in parallel using forkJoin
    forkJoin({
      connection: this.connectionsService.getConnection().pipe(
        catchError(() => of(null))
      ),
      rules: this.rulesService.listRules().pipe(
        catchError(() => of([]))
      ),
      templates: this.templatesService.listTemplates().pipe(
        catchError(() => of([]))
      )
    }).subscribe({
      next: (results) => {
        // Process connection
        if (results.connection) {
          this.connectionStatus = 'configured';
          this.connectionUrl = results.connection.confluence_base_url;
        } else {
          this.connectionStatus = 'not-configured';
        }

        // Process rules
        this.rulesCount = Array.isArray(results.rules) ? results.rules.length : 0;

        // Process templates
        this.templatesCount = Array.isArray(results.templates) ? results.templates.length : 0;

        this.isLoading = false;
      },
      error: () => {
        // On error, set defaults
        this.connectionStatus = 'not-configured';
        this.rulesCount = 0;
        this.templatesCount = 0;
        this.isLoading = false;
      }
    });
  }
}
