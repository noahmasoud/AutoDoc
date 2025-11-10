#!/usr/bin/env node
/**
 * TypeScript AST Parser Bridge Script
 * 
 * This script serves as a bridge between Python backend and TypeScript parser.
 * It uses @typescript-eslint/typescript-estree to parse TypeScript files
 * and outputs structured JSON AST for consumption by the Python backend.
 * 
 * Usage:
 *   node parse-typescript.js <file-path>
 *   echo "<code>" | node parse-typescript.js
 * 
 * Output: JSON AST to stdout
 * Errors: JSON error object to stderr
 */

const fs = require('fs');
const path = require('path');

// Import the parser (will be installed via npm)
let parse;

try {
  // Try to load the parser
  parse = require('@typescript-eslint/typescript-estree').parse;
} catch (error) {
  console.error(JSON.stringify({
    error: 'PARSER_NOT_FOUND',
    message: '@typescript-eslint/typescript-estree is not installed',
    details: 'Run: npm install @typescript-eslint/typescript-estree',
    originalError: error.message
  }));
  process.exit(1);
}

/**
 * Main parsing function
 */
function parseTypeScript(sourceCode, options = {}) {
  try {
    const ast = parse(sourceCode, {
      loc: true,              // Include line/column information
      range: true,            // Include character ranges
      tokens: false,          // Don't include token information (cleaner output)
      comment: false,         // Don't include comments (cleaner output)
      jsx: true,              // Support JSX syntax
      ...options
    });

    return {
      success: true,
      ast: ast
    };
  } catch (error) {
    return {
      success: false,
      error: {
        type: 'PARSE_ERROR',
        message: error.message,
        line: error.lineNumber || null,
        column: error.column || null
      }
    };
  }
}

/**
 * Read source code from file or stdin
 */
function getSourceCode(input) {
  // If input is a file path
  if (input && input.trim() && fs.existsSync(input)) {
    try {
      return fs.readFileSync(input, 'utf8');
    } catch (error) {
      console.error(JSON.stringify({
        error: 'FILE_READ_ERROR',
        message: `Cannot read file: ${input}`,
        details: error.message
      }));
      process.exit(1);
    }
  }
  
  // If input is empty or doesn't exist, try to read from stdin
  try {
    return fs.readFileSync(0, 'utf8'); // stdin file descriptor is 0
  } catch (error) {
    console.error(JSON.stringify({
      error: 'NO_INPUT',
      message: 'No file path provided and cannot read from stdin',
      details: error.message
    }));
    process.exit(1);
  }
}

/**
 * Main execution
 */
function main() {
  const args = process.argv.slice(2);
  
  // Get file path from command line or stdin
  const input = args[0] || null;
  
  // Get source code
  const sourceCode = getSourceCode(input);
  
  if (!sourceCode || sourceCode.trim().length === 0) {
    console.error(JSON.stringify({
      error: 'EMPTY_INPUT',
      message: 'Source code is empty'
    }));
    process.exit(1);
  }
  
  // Parse the TypeScript code
  const result = parseTypeScript(sourceCode);
  
  // Output JSON result to stdout
  console.log(JSON.stringify(result, null, 2));
  
  // Exit with appropriate code
  process.exit(result.success ? 0 : 1);
}

// Run if executed directly
if (require.main === module) {
  main();
}

// Export for testing
module.exports = { parseTypeScript, getSourceCode };

