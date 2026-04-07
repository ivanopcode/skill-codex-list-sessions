# skill-codex-list-sessions

Codex skill for listing recent local Codex sessions with full `session_id` values, compact per-session summaries, and optional exact lookup of trailing user messages.

## What It Does

- reads local Codex thread metadata from `~/.codex/state_5.sqlite`
- reads full user prompt history from `~/.codex/history.jsonl`
- returns recent top-level `cli` sessions by default
- supports exact `session_id` lookup
- supports keyword search such as `glab`, `youtrack`, or `worktree`
- can include internal `exec` and `subagent` sessions when explicitly requested
- defaults to a compact recent window of the latest `2` user messages per session
- instructs the agent to format list results as 3-line session blocks instead of wide tables

## Main Files

- `SKILL.md` — runtime instructions for Codex
- `agents/openai.yaml` — UI-facing metadata
- `locales/metadata.json` — localized user-facing metadata
- `.skill_triggers/<locale>.md` — localized trigger catalogs used to render `SKILL.md`
- `scripts/setup_main.py`, `scripts/setup_support.py` — managed global install flow
- `scripts/codex_sessions.py` — deterministic JSON-producing helper
- `scripts/codex-sessions` — thin shell wrapper

## Install

Install or update the managed copy with:

```bash
make install LOCALE=ru-en
```

This creates a managed runtime copy under `${XDG_DATA_HOME:-~/.local/share}/agents/skills/skill-codex-list-sessions`, renders localized metadata plus trigger previews from `.skill_triggers`, and refreshes the symlinks in `~/.claude/skills/skill-codex-list-sessions` and `~/.codex/skills/skill-codex-list-sessions`.

## Local Usage

```bash
./scripts/codex-sessions
./scripts/codex-sessions --limit 10
./scripts/codex-sessions --query glab --limit 5
./scripts/codex-sessions --session-id 019d4543-0d6c-7c50-9c21-b2fe17105c33
./scripts/codex-sessions --include-internal --limit 10
```

## License

MIT. See `LICENSE`.
