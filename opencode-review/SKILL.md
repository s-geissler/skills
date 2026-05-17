---
name: opencode-review
description: Delegate code reviews to an external model instead of doing self-reviews
---

# Opencode Review

Use `../bin/opencode-delegate.py` to dispatch external review work.

## Commands

### review — code review against requirements
```bash
../bin/opencode-delegate.py review --against <prd_or_issue_file> [--diff <patch>] [--paths <file>...] [--staged]
```
Use to verify code changes satisfy a PRD or issue document. Defaults to `git diff HEAD`; pass `--staged` to review staged changes only. Pass `--diff` to review a saved patch file, or `--paths` to review specific files. Returns exit code 1 if the review verdict is FAIL.
Use the "Reviewer" agent for these delegations.

## Options
- `-m provider/model` — optional model override (defaults to opencode's configured default)
- `--overwrite` — replace existing target file
