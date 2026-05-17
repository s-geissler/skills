# coding-skills

A collection of agent skills and a delegation helper for offloading LLM work.

## What's inside

| Path | Purpose |
|------|---------|
| `bin/opencode-delegate.py` | CLI tool to dispatch LLM queries via opencode (`ask`, `write`, `review`) |
| `opencode-delegate/SKILL.md` | Skill docs for the **delegate** skill — bulk analysis & boilerplate generation |
| `opencode-review/SKILL.md` | Skill docs for the **opencode-review** skill — external code review against PRDs/issues |

## `delegate.py`

A small Python wrapper around `opencode run` for three common workflows:

- **`ask`** — analyse files and answer questions  
  `opencode-delegate.py ask --paths src/*.py --question "What does this module do?"`

- **`write`** — generate boilerplate from a spec  
  `opencode-delegate.py write --spec "A pytest test for User.login" --target tests/test_user.py`

- **`review`** — review code changes against a requirements doc  
  `opencode-delegate.py review --against docs/PRD-123.md --staged`

Run `opencode-delegate.py --help` for full options.

## Skills

Drop the skill folders into your agent's skills directory (e.g. `~/.agents/skills`) to make them available to your agents. Place `delegate.py` somewhere your agents can find and run it (i.e. your project repo or PATH).

## License

MIT — see [LICENSE](LICENSE).
