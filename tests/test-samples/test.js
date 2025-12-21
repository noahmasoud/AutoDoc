/**
 * Test JavaScript file for analyzer testing
 */

// Function declaration
function testFunction(param1, param2) {
    return param1 + param2;
}

// Arrow function
const arrowFunction = (x, y) => x * y;

// Class declaration
class TestClass {
    constructor(name) {
        this.name = name;
    }

    getName() {
        return this.name;
    }
}

// Export
export { testFunction, TestClass };

