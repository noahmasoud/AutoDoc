/**
 * Basic exports test file
 * Tests simple export scenarios
 */

export interface BasicInterface {
  name: string;
  value: number;
}

export class BasicClass {
  private field: string;

  constructor(field: string) {
    this.field = field;
  }
}

export function basicFunction(param: string): string {
  return param.toUpperCase();
}

export type BasicType = string | number;

export enum BasicEnum {
  FIRST = "first",
  SECOND = "second",
}

