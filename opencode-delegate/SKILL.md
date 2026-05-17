---
name: opencode-delegate
description: Delegate basic tasks to a simple and cheap model using opencode oneshots
---

# Delegation Skill

Use `../bin/opencode-delegate.py` to dispatch heavy LLM work via the opencode CLI instead of burning your own context window.

## Commands

### ask — bulk file analysis
```bash
../bin/opencode-delegate.py ask --paths <file>... --question "<question>"
```
Use when reading >400 lines or 3+ files. Returns a structured summary. Prefer this over reading files yourself.
Use the "Reviewer" agent for these delegations.

### write — boilerplate generation
```bash
../bin/opencode-delegate.py write --spec "<what to generate>" --target <output> [--context <ref>...] [--overwrite]
```
Use for tests, config files, docstrings, repetitive patterns. Review output and edit only what needs fixing.
Use the "Dev" agent for these delegations.

## Options
- `-m provider/model` — optional model override (defaults to opencode's configured default)
- `--overwrite` — replace existing target file

## When NOT to delegate
- Tasks under ~2000 tokens (overhead not worth it)
- Architectural decisions, debugging, safety-critical code
- Anything requiring careful reasoning
- When exact line numbers are needed for editing

