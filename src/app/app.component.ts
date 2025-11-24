import { Component, OnInit } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter } from 'rxjs/operators';
import { NavbarComponent } from './components/navbar/navbar.component';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule, NavbarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'AutoDocProjectFE';
  showNavbar = false;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // Subscribe to auth status to show/hide navbar
    this.authService.getAuthStatus().subscribe(isAuth => {
      this.showNavbar = isAuth;
    });

    // Check current route and auth status on navigation
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.updateNavbarVisibility();
    });

    // Initial check
    this.updateNavbarVisibility();
  }

  private updateNavbarVisibility(): void {
    const currentRoute = this.router.url;
    // Don't show navbar on login page
    this.showNavbar = this.authService.isLoggedIn() && currentRoute !== '/login';
  }
}
