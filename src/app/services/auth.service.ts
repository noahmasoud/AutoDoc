import { Injectable } from '@angular/core';

@Injectable()
export class AuthService {
  private authenticated = false;

  loginPlaceholder() {
    this.authenticated = true;
    console.log('Auth: signed in (placeholder)');
  }

  logout() {
    this.authenticated = false;
    console.log('Auth: signed out (placeholder)');
  }

  isAuthenticated() {
    return this.authenticated;
  }
}
