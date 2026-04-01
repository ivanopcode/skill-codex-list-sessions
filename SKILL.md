---
name: skill-codex-list-sessions
description: Use when Codex needs to list recent local Codex sessions, find a session by topic or keyword, recover full session ids, or summarize what a session was generally about plus what the latest user messages said. Reads local Codex history from ~/.codex/state_5.sqlite and ~/.codex/history.jsonl through the bundled helper. Default to 20 top-level cli sessions unless the user asks for a different limit or explicitly wants internal exec or subagent sessions too.
---

# Codex Sessions

## Default Mode

- Execute the bundled helper yourself and return the result.
- Do not answer with shell recipes when the helper already exists locally.
- Show commands only when the user explicitly asks for setup or implementation details.
- Answer in the user's language unless the user explicitly asks for another language.
- Keep every `session_id` full. Never shorten it.
- For recent-session lists and topic searches, prefer compact summaries over verbatim raw message dumps.
- Show full raw last-message text only when the user explicitly asks for exact text, verbatim text, or a deep dive into one exact session.
- Treat "last messages" as the latest user prompts from local Codex history unless the user explicitly asks for a different interpretation.
- Resolve command paths from this skill file path.
- If the skill file path is `/abs/path/to/SKILL.md`, then:
  - `<sessions-command>` is `/abs/path/to/scripts/codex-sessions`
- Use that absolute path for every command in this skill.
- Do not replace the helper with ad hoc `sqlite3`, `rg`, or `python` commands unless the helper is missing or clearly insufficient.
- Before sending the final answer, do one completeness check against the user's request. If the answer is not good enough yet, keep using tools instead of finalizing.

## Repository Notes

- This repository is the source of truth for the skill.
- The local runtime skill may be exposed through symlinks such as:
  - `~/.codex/skills/skill-codex-list-sessions`
  - `~/.claude/skills/skill-codex-list-sessions`
- Keep the repository contents deterministic and weak-model-friendly.
- Prefer extending the bundled helper over adding long procedural prose when new read behavior is needed.

## Resolve Context First

Always start with the bundled helper.

Default recent-session read:

```bash
<sessions-command> --last-messages 2
```

That means:

- top-level `cli` sessions only
- `20` sessions
- `2` trailing user messages per session

Override the limit only when the user asked for a different number:

```bash
<sessions-command> --limit <n> --last-messages 2
```

If the user asks for more or fewer recent messages inside each session:

```bash
<sessions-command> --limit <n> --last-messages <m>
```

## Search By Topic Or Session Id

When the user is trying to find a specific session by topic, tool name, repo, or keyword, use `--query`:

```bash
<sessions-command> --query '<text>' --limit <n>
```

Examples:

- `glab`
- `youtrack`
- `worktree`
- `partners-app-dev`

When the user already knows the exact session id, use:

```bash
<sessions-command> --session-id <full-session-id>
```

Rules:

- Prefer `--session-id` over `--query` when the user already has the full id.
- Keep `--limit` explicit for broad searches so the result set stays intentional.
- If `--query` returns no top-level `cli` matches, rerun once with `--include-internal` before concluding that nothing was found.

## Internal Sessions

By default, recent-session lists should show only top-level `cli` sessions.

Use internal sessions only when one of these is true:

- the user explicitly asks for subagent, exec, or internal runs
- the user is searching a topic and the top-level pass returned no matches
- the user is debugging why a specific one-shot run existed

Command:

```bash
<sessions-command> --include-internal --limit <n>
<sessions-command> --include-internal --query '<text>' --limit <n>
```

Internal sessions include:

- `exec`
- `subagent`
- other non-`cli` thread sources

Say explicitly when a reported match came from an internal session rather than a normal top-level conversation.

## Summary Rules

The helper returns:

- full `session_id`
- `title`
- `topic_basis`
- `first_user_message`
- full trailing user messages
- timestamps
- cwd
- session kind

Use that data to produce two separate outputs for each session:

1. **Overall discussion**
   - one or two sentences about what the session was generally about
   - prefer the session `title` when it is descriptive
   - when the title is generic like `hello` or `привет`, infer the topic from `first_user_message` and the trailing messages instead
2. **Last two messages summary**
   - summarize what the latest two user messages were about in one sentence
   - do not paste the raw texts in list mode
   - mention exact raw texts only for exact lookup or when the user explicitly asked for verbatim output

## Compact Output First

For recent-session lists and topic searches, the default answer must be a compact Markdown table.

Use exactly these columns in the main table:

- `Session ID`
- `О чем вся беседа`
- `О чем последние 2 сообщения`

Rules:

- One row per session.
- Each summary cell should usually be one sentence.
- Do not dump raw quoted user messages into the table.
- Do not render the main answer as a long numbered essay unless the user explicitly asks for that format.
- After the table, add at most one short line that says how many sessions were returned and whether internal sessions were included.

Target shape:

```markdown
| Session ID | О чем вся беседа | О чем последние 2 сообщения |
| --- | --- | --- |
| 019d... | Сессия про ... | Последние два сообщения были про ... |
```

This compact table is the default for:

- recent-session lists
- keyword searches

For exact session lookup, use a short summary block first. Only after that, include the full raw latest messages when the user explicitly asked for exact text or deep inspection.

## Output Contract

For a recent-session list:

- include the total number of returned sessions
- list sessions in descending `updated_at` order
- use one compact Markdown table as the main output
- for each session include:
  - full `session_id`
  - overall discussion description
  - one-sentence summary of what the latest two user messages were about
- keep `session_id` complete and unshortened

For a search result:

- say what query was used
- say whether the match is top-level or internal
- if several sessions match, list all returned sessions up to the requested limit
- use the same compact Markdown table as the default presentation

For an exact session lookup:

- include the full `session_id`
- include the overall discussion description
- include a short summary of the latest two user messages
- include the raw latest user messages only when the user explicitly asked for exact text or the exact lookup clearly implies deep inspection
- mention if the session was not found exactly

## Ask Only If Blocked

Ask the user only when one of these is true:

- local Codex files are missing
- the user asked for a specific number but it is ambiguous or invalid
- the user asked for a different notion of "last messages" than the helper exposes from local history

Otherwise, run the helper and return the result.

## Pre-final Check

Before sending the final answer:

1. Confirm that every shown `session_id` is full.
2. Confirm that list and search results are shown as one compact Markdown table rather than a long numbered list.
3. Confirm that overall discussion and "last two messages" are separated clearly.
4. Confirm that the session count matches the requested or default limit.
5. Confirm that you did not silently include internal sessions unless the rules above allow it.
6. Confirm that you did not paste raw full messages in list or search mode unless the user explicitly asked for exact text.

If any answer is "no", keep working instead of finalizing.
