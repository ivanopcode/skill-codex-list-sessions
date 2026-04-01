#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_STATE_DB = Path.home() / ".codex" / "state_5.sqlite"
DEFAULT_HISTORY_FILE = Path.home() / ".codex" / "history.jsonl"
DEFAULT_LIMIT = 20
DEFAULT_LAST_MESSAGES = 3
GENERIC_TITLES = {
    "",
    ".",
    ":q",
    "hello",
    "hi",
    "hey",
    "привет",
    "привет привет",
}


class CodexSessionsError(RuntimeError):
    pass


@dataclass(frozen=True)
class ThreadRow:
    session_id: str
    title: str
    created_at: int
    updated_at: int
    cwd: str
    source: str
    first_user_message: str


@dataclass(frozen=True)
class UserMessage:
    ts: int
    text: str


def fail(message: str) -> None:
    raise CodexSessionsError(message)


def existing_file(path: Path, description: str) -> Path:
    if not path.is_file():
        fail(f"{description} not found: {path}")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codex-sessions",
        description=(
            "List local Codex sessions from ~/.codex/state_5.sqlite and ~/.codex/history.jsonl. "
            "Defaults to top-level cli sessions only."
        ),
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="How many sessions to return. Default: 20.")
    parser.add_argument(
        "--last-messages",
        type=int,
        default=DEFAULT_LAST_MESSAGES,
        help="How many trailing user messages to include for each session. Default: 3.",
    )
    parser.add_argument(
        "--query",
        help="Case-insensitive filter over session title and full user message texts.",
    )
    parser.add_argument(
        "--session-id",
        help="Return one exact session id instead of a generic recent-session list.",
    )
    parser.add_argument(
        "--include-internal",
        action="store_true",
        help="Include internal exec and subagent sessions in addition to top-level cli sessions.",
    )
    parser.add_argument(
        "--state-db",
        type=Path,
        default=DEFAULT_STATE_DB,
        help="Path to Codex state SQLite database. Default: ~/.codex/state_5.sqlite",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=DEFAULT_HISTORY_FILE,
        help="Path to Codex history JSONL file. Default: ~/.codex/history.jsonl",
    )
    return parser.parse_args()


def normalize_message_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def parse_source_kind(source: str) -> str:
    if source == "cli":
        return "cli"
    if source == "exec":
        return "exec"

    if source.startswith("{"):
        try:
            payload = json.loads(source)
        except json.JSONDecodeError:
            return "other"

        if isinstance(payload, dict) and "subagent" in payload:
            return "subagent"

    return "other"


def title_is_generic(title: str) -> bool:
    return title.strip().casefold() in GENERIC_TITLES


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def load_threads(db_path: Path) -> list[ThreadRow]:
    existing_file(db_path, "Codex state database")
    with connect_readonly(db_path) as con:
        rows = con.execute(
            """
            select id, title, created_at, updated_at, cwd, source, first_user_message
            from threads
            order by updated_at desc, id desc
            """
        ).fetchall()

    return [
        ThreadRow(
            session_id=row[0],
            title=row[1] or "",
            created_at=int(row[2]),
            updated_at=int(row[3]),
            cwd=row[4] or "",
            source=row[5] or "",
            first_user_message=row[6] or "",
        )
        for row in rows
    ]


def load_user_history(history_path: Path) -> dict[str, list[UserMessage]]:
    existing_file(history_path, "Codex history file")
    sessions: dict[str, list[UserMessage]] = defaultdict(list)

    with history_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            session_id = payload.get("session_id")
            ts = payload.get("ts")
            text = payload.get("text")

            if not isinstance(session_id, str) or not isinstance(ts, int) or not isinstance(text, str):
                continue

            sessions[session_id].append(UserMessage(ts=ts, text=normalize_message_text(text)))

    for messages in sessions.values():
        messages.sort(key=lambda item: item.ts)

    return sessions


def matches_query(query: str | None, thread: ThreadRow, messages: list[UserMessage]) -> bool:
    if not query:
        return True

    needle = query.casefold()
    if needle in thread.title.casefold():
        return True
    if needle in thread.first_user_message.casefold():
        return True

    return any(needle in message.text.casefold() for message in messages)


def topic_basis(thread: ThreadRow, messages: list[UserMessage]) -> str:
    if thread.title and not title_is_generic(thread.title):
        return thread.title
    if thread.first_user_message:
        return thread.first_user_message
    if messages:
        return messages[0].text
    return thread.title


def should_include_thread(thread: ThreadRow, include_internal: bool) -> bool:
    kind = parse_source_kind(thread.source)
    if include_internal:
        return True
    return kind == "cli"


def build_session_payload(
    thread: ThreadRow,
    messages: list[UserMessage],
    last_messages: int,
) -> dict[str, Any]:
    trailing = messages[-last_messages:] if last_messages > 0 else []

    return {
        "session_id": thread.session_id,
        "session_kind": parse_source_kind(thread.source),
        "source": thread.source,
        "title": thread.title,
        "title_is_generic": title_is_generic(thread.title),
        "topic_basis": topic_basis(thread, messages),
        "created_at_epoch": thread.created_at,
        "created_at": to_iso(thread.created_at),
        "updated_at_epoch": thread.updated_at,
        "updated_at": to_iso(thread.updated_at),
        "cwd": thread.cwd,
        "first_user_message": thread.first_user_message,
        "user_message_count": len(messages),
        "last_user_messages": [
            {
                "ts_epoch": message.ts,
                "ts": to_iso(message.ts),
                "text": message.text,
            }
            for message in trailing
        ],
    }


def main() -> int:
    args = parse_args()

    if args.limit <= 0:
        fail("--limit must be greater than 0")
    if args.last_messages < 0:
        fail("--last-messages cannot be negative")

    threads = load_threads(args.state_db.expanduser().resolve())
    history = load_user_history(args.history_file.expanduser().resolve())

    sessions: list[dict[str, Any]] = []
    for thread in threads:
        if args.session_id and thread.session_id != args.session_id:
            continue
        if not should_include_thread(thread, args.include_internal):
            continue

        messages = history.get(thread.session_id, [])
        if not matches_query(args.query, thread, messages):
            continue

        sessions.append(build_session_payload(thread, messages, args.last_messages))
        if not args.session_id and len(sessions) >= args.limit:
            break

    payload = {
        "limit": args.limit,
        "last_messages": args.last_messages,
        "query": args.query,
        "session_id": args.session_id,
        "include_internal": args.include_internal,
        "state_db": str(args.state_db.expanduser().resolve()),
        "history_file": str(args.history_file.expanduser().resolve()),
        "returned": len(sessions),
        "sessions": sessions,
    }

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CodexSessionsError as error:
        print(f"codex-sessions: {error}", file=sys.stderr)
        raise SystemExit(1)
