# Contributing

## Branching Strategy

- `main` = production. Keep this branch stable and release-ready at all times.
- `develop` = integration branch. Completed feature work lands here first.
- `feature/*` = short-lived branches for planned work. Always create these from `develop`.
- `hotfix/*` = emergency production fixes. Create these from `main` only when production needs an urgent fix.

## Feature Workflow

1. Update your local refs: `git fetch origin`
2. Switch to `develop`: `git switch develop`
3. Pull the latest integration code: `git pull origin develop`
4. Create your feature branch: `git switch -c feature/<name>`
5. Do your work, commit cleanly, and push your branch.
6. Open a pull request into `develop`.
7. After review and testing, merge into `develop`.
8. Release to production only through a separate pull request from `develop` to `main`.

## Rules

- Never branch from `main` for feature work.
- Always branch from `develop` for features and normal bug fixes.
- Pull requests go to `develop` unless the change is a hotfix or a release.
- Only release pull requests go from `develop` to `main`.
- Keep `main` stable, protected, and limited to reviewed release or hotfix changes.

## Example Commands

```bash
git fetch origin
git switch develop
git pull origin develop
git switch -c feature/cart-discount-rules
git push -u origin feature/cart-discount-rules
```

Open the PR with:

```text
base: develop
compare: feature/cart-discount-rules
```

For a hotfix:

```bash
git fetch origin
git switch main
git pull origin main
git switch -c hotfix/payment-timeout-fix
```

## Mental Model

Build on `develop`.

Stabilize and test in `develop`.

Release from `develop` to `main`.
