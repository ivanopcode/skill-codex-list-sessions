from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import codex_sessions as cs


class CodexSessionsTest(unittest.TestCase):
    def test_title_is_generic(self) -> None:
        self.assertTrue(cs.title_is_generic("hello"))
        self.assertFalse(cs.title_is_generic("Investigate GitLab skill"))

    def test_build_session_payload_keeps_full_session_id_and_trailing_messages(self) -> None:
        thread = cs.ThreadRow(
            session_id="019d4543-0d6c-7c50-9c21-b2fe17105c33",
            title="Investigate GitLab skill",
            created_at=1_700_000_000,
            updated_at=1_700_000_100,
            cwd="/tmp/repo",
            source="cli",
            first_user_message="Check recent GitLab changes",
        )
        messages = [
            cs.UserMessage(ts=1_700_000_010, text="Check recent GitLab changes"),
            cs.UserMessage(ts=1_700_000_020, text="Summarize the last two prompts"),
            cs.UserMessage(ts=1_700_000_030, text="Keep full session ids"),
        ]

        payload = cs.build_session_payload(thread, messages, last_messages=2)

        self.assertEqual(payload["session_id"], "019d4543-0d6c-7c50-9c21-b2fe17105c33")
        self.assertEqual(len(payload["last_user_messages"]), 2)
        self.assertEqual(payload["last_user_messages"][0]["text"], "Summarize the last two prompts")
        self.assertEqual(payload["last_user_messages"][1]["text"], "Keep full session ids")
