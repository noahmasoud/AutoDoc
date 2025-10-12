import { Routes } from '@angular/router';
import { AuthGuard } from './services/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', loadChildren: () => import('./pages/dashboard/dashboard.module').then(m => m.DashboardModule), canActivate: [AuthGuard] },
  { path: 'connections', loadChildren: () => import('./pages/connections/connections.module').then(m => m.ConnectionsModule), canActivate: [AuthGuard] },
  { path: 'rules', loadChildren: () => import('./pages/rules/rules.module').then(m => m.RulesModule), canActivate: [AuthGuard] },
  { path: 'templates', loadChildren: () => import('./pages/templates/templates.module').then(m => m.TemplatesModule), canActivate: [AuthGuard] },
  { path: 'code-testing', loadChildren: () => import('./pages/code-testing/code-testing.module').then(m => m.CodeTestingModule), canActivate: [AuthGuard] },
  { path: 'auto-doc', loadChildren: () => import('./pages/auto-doc/auto-doc.module').then(m => m.AutoDocModule), canActivate: [AuthGuard] },
  { path: 'confluence', loadChildren: () => import('./pages/confluence/confluence.module').then(m => m.ConfluenceModule), canActivate: [AuthGuard] },
  { path: 'settings', loadChildren: () => import('./pages/settings/settings.module').then(m => m.SettingsModule), canActivate: [AuthGuard] },
  { path: '**', redirectTo: 'dashboard' }
];
