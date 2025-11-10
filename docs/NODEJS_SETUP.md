# Node.js Setup for TypeScript Parser

## Installation Required

The TypeScript AST parser requires Node.js to be installed on the system.

## Install Node.js

### macOS (using Homebrew)
```bash
brew install node
```

### Verify Installation
```bash
node --version  # Should be >= 18.0.0
npm --version
```

## Install Parser Dependencies

After Node.js is installed, run:

```bash
npm install
```

This will install:
- `@typescript-eslint/typescript-estree` - TypeScript parser

## Test the Parser

After installation, test the parser:

```bash
# Test with the test script
npm test

# Or manually
node scripts/parse-typescript.js tests/test-samples/example.ts
```

## Docker Alternative

If you prefer not to install Node.js locally, you can use Docker:

```bash
# Run parser via Docker
docker run --rm -v $(pwd):/app -w /app node:18 npm install
docker run --rm -v $(pwd):/app -w /app node:18 node scripts/parse-typescript.js tests/test-samples/example.ts
```

## CI/CD Usage

For CI/CD pipelines, Node.js can be installed as part of the workflow:

```yaml
# Example GitHub Actions step
- name: Setup Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '18'
    
- name: Install parser dependencies
  run: npm install
```

