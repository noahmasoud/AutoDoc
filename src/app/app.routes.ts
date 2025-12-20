import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ConnectionsComponent } from './pages/connections/connections.component';
import { LLMConfigComponent } from './pages/llm-config/llm-config.component';
import { RulesComponent } from './pages/rules/rules.component';
import { TemplatesComponent } from './pages/templates/templates.component';
import { PromptsComponent } from './pages/prompts/prompts.component';
import { LoginComponent } from './pages/login/login.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { 
    path: 'dashboard', 
    component: DashboardComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'connections', 
    component: ConnectionsComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'llm-config', 
    component: LLMConfigComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'rules', 
    component: RulesComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'templates', 
    component: TemplatesComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'prompts', 
    component: PromptsComponent, 
    canActivate: [authGuard] 
  },
  {
    path: 'runs/:runId',
    loadChildren: () =>
      import('./pages/run-details/run-details.module').then(
        (m) => m.RunDetailsModule
      ),
    canActivate: [authGuard]
  },
  {
    path: 'runs/:runId/patches/:patchId',
    loadChildren: () =>
      import('./pages/patch-preview/patch-preview.module').then(
        (m) => m.PatchPreviewModule
      ),
    canActivate: [authGuard]
  },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: 'dashboard' },
];
