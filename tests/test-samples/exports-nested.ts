/**
 * Nested exports test file
 * Tests exports within namespaces/modules
 */

export namespace OuterNamespace {
  export interface NestedInterface {
    data: string;
  }

  export class NestedClass {
    private value: number = 0;
  }

  export function nestedFunction(): void {
    console.log("Nested function");
  }

  export namespace InnerNamespace {
    export const INNER_CONSTANT = "inner";
  }
}

export module TestModule {
  export type ModuleType = string;
  export enum ModuleEnum {
    VALUE1 = "value1",
    VALUE2 = "value2",
  }
}

