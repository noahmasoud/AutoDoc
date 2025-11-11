/**
 * Default exports test file
 * Tests default export scenarios
 */

export default class DefaultClass {
  public name: string = "default";

  public getValue(): string {
    return this.name;
  }
}

export interface NamedInterface {
  prop: string;
}

// Named export alongside default
export function namedFunction(): number {
  return 42;
}

