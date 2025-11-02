#!/usr/bin/env node
/**
 * Test script for TypeScript parser
 * 
 * Tests the parser with various TypeScript constructs:
 * - Classes
 * - Decorators
 * - Generics
 * - Async functions
 * - ES modules
 * - Type annotations
 */

const { parseTypeScript } = require('../scripts/parse-typescript');

// Test case 1: Simple class
const test1 = `
export class MyClass {
  private name: string;
  
  constructor(name: string) {
    this.name = name;
  }
  
  getName(): string {
    return this.name;
  }
}
`;

// Test case 2: Class with decorators
const test2 = `
import { Component } from '@angular/core';

@Component({
  selector: 'app-my-component',
  templateUrl: './my-component.html'
})
export class MyComponent {
  @Input() title: string = '';
  
  ngOnInit(): void {
    console.log('Component initialized');
  }
}
`;

// Test case 3: Generics and async
const test3 = `
export class DataService {
  async fetchData<T>(url: string): Promise<T> {
    const response = await fetch(url);
    return response.json();
  }
  
  processItems<T extends { id: number }>(items: T[]): T[] {
    return items.filter(item => item.id > 0);
  }
}
`;

// Test case 4: Interface and type definitions
const test4 = `
export interface User {
  id: number;
  name: string;
  email: string;
}

export type Status = 'active' | 'inactive' | 'pending';

export function createUser(user: Partial<User>): User {
  return {
    id: 0,
    name: user.name || '',
    email: user.email || ''
  };
}
`;

// Test case 5: Complex example with all features
const test5 = `
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl: string = 'https://api.example.com';
  
  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    const response = await fetch(\`\${this.baseUrl}/\${endpoint}\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    return {
      data: await response.json(),
      status: response.status,
      message: response.statusText
    };
  }
  
  getObservable<T>(endpoint: string): Observable<T> {
    // Implementation would go here
    return new Observable();
  }
}
`;

// Run tests
const tests = [
  { name: 'Simple Class', code: test1 },
  { name: 'Decorated Component', code: test2 },
  { name: 'Generics and Async', code: test3 },
  { name: 'Interfaces and Types', code: test4 },
  { name: 'Complex Example', code: test5 }
];

console.log('🧪 Testing TypeScript Parser\n');
console.log('='.repeat(50));

let passed = 0;
let failed = 0;

tests.forEach((test, index) => {
  console.log(`\nTest ${index + 1}: ${test.name}`);
  console.log('-'.repeat(50));
  
  const result = parseTypeScript(test.code);
  
  if (result.success) {
    console.log('✅ PASSED');
    console.log(`   - AST type: ${result.ast.type}`);
    console.log(`   - Body length: ${result.ast.body?.length || 0}`);
    passed++;
  } else {
    console.log('❌ FAILED');
    console.log(`   - Error: ${result.error.message}`);
    failed++;
  }
});

console.log('\n' + '='.repeat(50));
console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);

if (failed === 0) {
  console.log('🎉 All tests passed!\n');
  process.exit(0);
} else {
  console.log('⚠️  Some tests failed\n');
  process.exit(1);
}

