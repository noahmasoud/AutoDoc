import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';

import { AppComponent } from './components/app.component';
import { NavComponent } from './components/nav/nav.component';
import { routes } from './app.routes';
import { AuthService } from './services/auth.service';
import { AuthGuard } from './services/auth.guard';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { RetryInterceptor } from './interceptors/retry.interceptor';

import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ConnectionsComponent } from './components/connections/connections.component';
import { RulesComponent } from './components/rules/rules.component';
import { TemplatesComponent } from './components/templates/templates.component';
import { AuthComponent } from './components/auth/auth.component';

@NgModule({
  declarations: [
    AppComponent,
    NavComponent,
    DashboardComponent,
    ConnectionsComponent,
    RulesComponent,
    TemplatesComponent,
    AuthComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    RouterModule.forRoot(routes)
  ],
  providers: [
    AuthService,
    AuthGuard,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: RetryInterceptor,
      multi: true,
    },
    provideAnimationsAsync(),
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
