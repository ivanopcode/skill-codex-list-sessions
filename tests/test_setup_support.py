from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import setup_support as ss


class SetupSupportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)

    def make_source_skill_dir(self) -> Path:
        skill_dir = self.root / "source" / "skill-codex-list-sessions"
        (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
        (skill_dir / "locales").mkdir(parents=True, exist_ok=True)
        (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (skill_dir / ".git").mkdir(parents=True, exist_ok=True)

        (skill_dir / "README.md").write_text("readme\n", encoding="utf-8")
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: skill-codex-list-sessions\n"
            "description: English source description\n"
            "triggers:\n"
            '  - "codex sessions"\n'
            "---\n\n"
            "# Sample Skill\n",
            encoding="utf-8",
        )
        (skill_dir / "agents" / "openai.yaml").write_text(
            'interface:\n'
            '  display_name: "skill-codex-list-sessions"\n'
            '  short_description: "English Short"\n'
            '  default_prompt: "Use $skill-codex-list-sessions in English."\n',
            encoding="utf-8",
        )
        (skill_dir / "locales" / "metadata.json").write_text(
            json.dumps(
                {
                    "locales": {
                        "en": {
                            "description": "English localized description",
                            "display_name": "skill-codex-list-sessions",
                            "short_description": "English Short",
                            "default_prompt": "Use $skill-codex-list-sessions in English.",
                            "local_prefix": "[local] ",
                        },
                        "ru": {
                            "description": "Русское описание",
                            "display_name": "skill-codex-list-sessions",
                            "short_description": "Русский Short",
                            "default_prompt": "Используй $skill-codex-list-sessions по-русски.",
                            "local_prefix": "[локально] ",
                        },
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (skill_dir / ".skill_triggers").mkdir(parents=True, exist_ok=True)
        (skill_dir / ".skill_triggers" / "en.md").write_text(
            "- skill-codex-list-sessions\n- codex sessions\n- recent codex sessions\n- list codex sessions\n- find codex session\n- codex session id\n- latest codex sessions\n",
            encoding="utf-8",
        )
        (skill_dir / ".skill_triggers" / "ru.md").write_text(
            "- сессии codex\n- последние сессии codex\n- показать сессии codex\n- найди сессию codex\n- session id codex\n- последние сообщения codex\n- история сессий codex\n",
            encoding="utf-8",
        )
        (skill_dir / "scripts" / "codex_sessions.py").write_text("print('ok')\n", encoding="utf-8")
        (skill_dir / "scripts" / "codex-sessions").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        (skill_dir / ".git" / "config").write_text("", encoding="utf-8")
        return skill_dir

    def test_render_skill_metadata_dual_mode_merges_trigger_lists(self) -> None:
        skill_dir = self.make_source_skill_dir()

        ss.render_skill_metadata(skill_dir, "ru-en")

        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            'description: "Русское описание Триггеры: \\"сессии codex\\", \\"последние сессии codex\\", \\"показать сессии codex\\", \\"найди сессию codex\\", \\"session id codex\\", \\"последние сообщения codex\\". / English localized description Triggers: \\"skill-codex-list-sessions\\", \\"codex sessions\\", \\"recent codex sessions\\", \\"list codex sessions\\", \\"find codex session\\", \\"codex session id\\"."',
            skill_text,
        )

    def test_load_metadata_catalog_rejects_trigger_lists_in_metadata_json(self) -> None:
        source_dir = self.make_source_skill_dir()
        metadata_path = source_dir / "locales" / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["locales"]["en"]["triggers"] = ["legacy trigger"]
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(ss.SetupError):
            ss.load_metadata_catalog(source_dir)

    def test_perform_install_creates_runtime_and_links(self) -> None:
        source_dir = self.make_source_skill_dir()
        home_dir = self.root / "home"
        xdg_data_home = self.root / "xdg-data"

        with mock.patch.dict(os.environ, {"HOME": str(home_dir), "XDG_DATA_HOME": str(xdg_data_home)}, clear=False):
            result = ss.perform_install(source_dir=source_dir, requested_locale="ru")

        self.assertEqual(result.runtime_dir, xdg_data_home / "agents" / "skills" / "skill-codex-list-sessions")
        self.assertTrue(result.claude_link.is_symlink())
        self.assertTrue(result.codex_link.is_symlink())
        manifest = json.loads((result.runtime_dir / ss.MANIFEST_FILENAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["source_dir"], str(source_dir.resolve()))


if __name__ == "__main__":
    unittest.main()
