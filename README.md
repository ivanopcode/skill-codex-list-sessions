# skill-codex-list-sessions

Weak-model-friendly Codex skill for listing recent local Codex sessions with full `session_id` values, session-level discussion summaries, and full trailing user messages.

## Author

Ivan Oparin  
GitHub: [@ivanopcode](https://github.com/ivanopcode)

## What It Does

- reads local Codex thread metadata from `~/.codex/state_5.sqlite`
- reads full user prompt history from `~/.codex/history.jsonl`
- returns recent top-level `cli` sessions by default
- supports exact `session_id` lookup
- supports keyword search such as `glab`, `youtrack`, or `worktree`
- can include internal `exec` and `subagent` sessions when explicitly requested

## Main Files

- `SKILL.md` — runtime instructions for Codex
- `agents/openai.yaml` — UI-facing metadata
- `scripts/codex_sessions.py` — deterministic JSON-producing helper
- `scripts/codex-sessions` — thin shell wrapper

## Local Usage

```bash
./scripts/codex-sessions
./scripts/codex-sessions --limit 10
./scripts/codex-sessions --query glab --limit 5
./scripts/codex-sessions --session-id 019d4543-0d6c-7c50-9c21-b2fe17105c33
./scripts/codex-sessions --include-internal --limit 10
```

## Skill Runtime Paths

Typical local symlinks:

- `~/.codex/skills/skill-codex-list-sessions`
- `~/.claude/skills/skill-codex-list-sessions`

## License

MIT. See `LICENSE`.
