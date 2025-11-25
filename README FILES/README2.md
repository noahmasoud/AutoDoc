# AutoDoc

Automated Documentation Updates for CI/CD Pipelines

## CI/CD Status

### GitHub Actions
![AutoDoc CI](https://github.com/YOUR-USERNAME/YOUR-REPO/workflows/AutoDoc%20CI/badge.svg)

### GitLab CI
*(Badge will be added when GitLab repo is configured)*

## Quick Start

### GitHub Actions Setup

Add to `.github/workflows/autodoc.yml`:

\`\`\`yaml
name: AutoDoc

on:
  pull_request:
  push:
    branches: [main, dev]

jobs:
  autodoc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run AutoDoc
        run: echo "AutoDoc running!"
\`\`\`

### GitLab CI Setup

Add to `.gitlab-ci.yml`:

\`\`\`yaml
stages:
  - test

autodoc:
  stage: test
  script:
    - echo "AutoDoc running!"
\`\`\`

## Sprint 0 Progress

- [x] SCRUM-6: GitHub Actions & GitLab CI pipeline structure
- [ ] SCRUM-8: Entrypoint script
- [ ] SCRUM-7: Docker image
- [ ] SCRUM-9: Integration testing

## Team

- Noah Masoud - Infrastructure & CI/CD
- Ryan Mitchell - Backend Development
- Logan Lay - Frontend Development