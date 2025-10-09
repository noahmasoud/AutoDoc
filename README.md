For a 3-person team working on a project with distinct infrastructure, backend, and frontend responsibilities, here's a practical branching strategy:
Recommended Strategy: Simplified Git Flow
main (protected)
├── develop (integration branch)
    ├── infrastructure/feature-name (Noah's branches)
    ├── backend/feature-name (Ryan's branches)
    └── frontend/feature-name (Logan's branches)
Branch Structure
Main Branches:

main - Production-ready code, protected, requires PR reviews
develop - Integration branch where all features merge first

Feature Branches:

infrastructure/ci-pipeline-setup
infrastructure/docker-optimization
backend/python-analyzer
backend/confluence-client
frontend/dashboard-ui
frontend/patch-preview

Why NOT separate long-lived branches for infra/be/fe?
Having permanent infrastructure, backend, and frontend branches creates problems:

Merge conflicts multiply - Three branches constantly diverging from each other
Integration happens too late - You don't discover conflicts until end of sprint
CI/CD complexity - Which branch do you deploy? Which one triggers tests?
Unclear "source of truth" - Is develop ahead of backend? Which is correct?

Workflow
bash# Noah starting a new feature
git checkout develop
git pull origin develop
git checkout -b infrastructure/github-actions-setup

# Work on feature...
git add .
git commit -m "feat(ci): add GitHub Actions workflow structure"
git push origin infrastructure/github-actions-setup

# Create PR: infrastructure/github-actions-setup → develop
Pull Request Rules

All PRs merge to develop first
Require at least 1 review from another team member
CI must pass (tests, linting) before merge
At end of sprint: Create PR from develop → main

Sprint Workflow
During Sprint:

Everyone works on feature branches
Merge completed features to develop throughout sprint
develop = current working state of sprint

End of Sprint:

Sprint review with working code on develop
If sprint is successful: merge develop → main
Tag release: git tag v0.1.0-sprint0

Handling Dependencies
When Ryan needs Noah's Docker image:
bash# Ryan creates branch from develop (which has Noah's merged work)
git checkout develop
git pull origin develop
git checkout -b backend/python-analyzer

# If Noah's work isn't merged yet, Ryan can temporarily branch from Noah's branch:
git checkout infrastructure/docker-optimization
git checkout -b backend/python-analyzer
# Later rebase onto develop when Noah's work merges
Branch Naming Convention
<area>/<ticket-number>-<short-description>

Examples:
infrastructure/AUTODOC-1-github-actions
backend/AUTODOC-10-python-ast-parser
frontend/AUTODOC-30-dashboard-ui
Protection Rules (GitHub/GitLab)
main branch:

Require PR reviews (1+ approvals)
Require status checks (CI must pass)
No direct pushes
No force pushes

develop branch:

Require PR reviews (1 approval recommended)
Require status checks
Allow force push only for rebase (use carefully)

When Things Go Wrong
Merge conflict in develop:
bashgit checkout develop
git pull origin develop
git checkout backend/my-feature
git rebase develop
... (50 lines left)