/**
 * Example TypeScript file for testing AutoDoc parser
 * 
 * This file demonstrates various TypeScript features that the parser
 * should be able to handle correctly.
 */

import { Injectable, Component, Input, Output, EventEmitter } from '@angular/core';
import { Observable } from 'rxjs';

// Interface definition
export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

// Type alias
export type Status = 'active' | 'inactive' | 'pending';

// Service class with decorator
@Injectable({
  providedIn: 'root'
})
export class UserService {
  private baseUrl: string = 'https://api.example.com';
  
  /**
   * Fetch user by ID
   */
  async getUserById(id: number): Promise<User> {
    const response = await fetch(`${this.baseUrl}/users/${id}`);
    return response.json();
  }
  
  /**
   * Fetch all users with optional filter
   */
  getUsers(filter?: Partial<User>): Observable<User[]> {
    // Implementation would go here
    return new Observable();
  }
  
  /**
   * Create a new user
   */
  async createUser(userData: Partial<User>): Promise<User> {
    const response = await fetch(`${this.baseUrl}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    
    return response.json();
  }
  
  /**
   * Generic method for API calls
   */
  async apiCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`, options);
    return response.json();
  }
}

// Component class with decorator
@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
  styleUrls: ['./user-list.component.css']
})
export class UserListComponent {
  @Input() users: User[] = [];
  @Output() userSelected = new EventEmitter<User>();
  
  selectedUser: User | null = null;
  
  ngOnInit(): void {
    console.log('Component initialized');
  }
  
  onUserClick(user: User): void {
    this.selectedUser = user;
    this.userSelected.emit(user);
  }
}

// Utility function
export function formatUserName(user: User): string {
  return `${user.name} (${user.email})`;
}

// Generic utility class
export class DataProcessor<T> {
  private data: T[];
  
  constructor(data: T[]) {
    this.data = data;
  }
  
  filter(predicate: (item: T) => boolean): T[] {
    return this.data.filter(predicate);
  }
  
  map<U>(mapper: (item: T) => U): U[] {
    return this.data.map(mapper);
  }
}

