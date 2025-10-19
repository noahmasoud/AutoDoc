import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ConnectionsComponent } from './pages/connections/connections.component';
import { RulesComponent } from './pages/rules/rules.component';
import { TemplatesComponent } from './pages/templates/templates.component';
import { AuthComponent } from './auth/auth.component';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'connections', component: ConnectionsComponent },
  { path: 'rules', component: RulesComponent },
  { path: 'templates', component: TemplatesComponent },
  {path: 'auth', component: AuthComponent },
];
