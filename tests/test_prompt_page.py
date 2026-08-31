from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "skills" / "zhiphoto" / "scripts" / "prompt_page.py"


class PromptPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temporary_directory.name)
        self.module_name = f"prompt_page_fixture_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(self.module_name, SCRIPT_PATH)
        if spec is None or spec.loader is None:
            self.fail("could not load prompt_page.py")
        self.prompt_page_module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_name] = self.prompt_page_module
        spec.loader.exec_module(self.prompt_page_module)

    def tearDown(self) -> None:
        sys.modules.pop(self.module_name, None)
        self.temporary_directory.cleanup()

    def _hash(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]

    def _write_batch_fixture(self, batch_dict: dict) -> Path:
        path = self.temp_dir / "batch.json"
        path.write_text(json.dumps(batch_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def _minimal_batch(self, **overrides) -> dict:
        prompt = overrides.pop("prompt", "Test prompt text")
        batch_dict = {
            "schema": "zhiphoto-prompt-batch/v1",
            "batch_id": "prompts-test-batch-20260831T1200",
            "created_at": "2026-08-31T12:00 (local)",
            "brief": "generate N prompts for testing",
            "entries": [
                {
                    "index": 1,
                    "anchor": "shot topic",
                    "kind": "generation",
                    "type": "window-light-portrait",
                    "profile": "natural-close-up",
                    "prompt": prompt,
                    "prompt_hash": self._hash(prompt),
                    "reference": {"policy": "optional", "role": "likeness", "expected": False, "instruction": ""},
                    "tested": False,
                    "tested_at": None,
                    "note": "",
                }
            ],
        }
        # Apply overrides to entries[0] if provided
        for key, value in overrides.items():
            batch_dict["entries"][0][key] = value
        return batch_dict

    def _assert_prompt_page_error(self, message_fragment: str, callable_obj, *args) -> None:
        with self.assertRaises(self.prompt_page_module.PromptPageError) as context:
            callable_obj(*args)
        self.assertIn(message_fragment, str(context.exception))

    def test_load_batch_schema_validation(self) -> None:
        batch_dict = self._minimal_batch()
        path = self._write_batch_fixture(batch_dict)
        batch = self.prompt_page_module.load_batch(path)
        self.assertEqual(batch.batch_id, "prompts-test-batch-20260831T1200")
        self.assertEqual(batch.brief, "generate N prompts for testing")
        self.assertEqual(len(batch.entries), 1)
        self.assertEqual(batch.entries[0].anchor, "shot topic")

    def test_load_batch_rejects_wrong_schema(self) -> None:
        batch_dict = self._minimal_batch()
        batch_dict["schema"] = "zhiphoto-prompt-batch/v2"
        path = self._write_batch_fixture(batch_dict)
        self._assert_prompt_page_error("schema must be exactly", self.prompt_page_module.load_batch, path)

    def test_load_batch_rejects_missing_entry_field(self) -> None:
        batch_dict = self._minimal_batch()
        del batch_dict["entries"][0]["anchor"]
        path = self._write_batch_fixture(batch_dict)
        self._assert_prompt_page_error("missing", self.prompt_page_module.load_batch, path)

    def test_render_html_is_deterministic(self) -> None:
        batch_dict = self._minimal_batch()
        path = self._write_batch_fixture(batch_dict)
        batch = self.prompt_page_module.load_batch(path)
        html1 = self.prompt_page_module.render_html(batch)
        html2 = self.prompt_page_module.render_html(batch)
        self.assertEqual(html1, html2)

    def test_render_html_is_deterministic_via_cli(self) -> None:
        batch_dict = self._minimal_batch()
        batch_path = self._write_batch_fixture(batch_dict)
        out_path_1 = self.temp_dir / "output1.html"
        out_path_2 = self.temp_dir / "output2.html"
        subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "render", "--batch", str(batch_path), "--out", str(out_path_1)],
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "render", "--batch", str(batch_path), "--out", str(out_path_2)],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(out_path_1.read_bytes(), out_path_2.read_bytes())

    def test_hash_stability_and_edit_invalidation(self) -> None:
        prompt = "Original prompt text"
        batch_dict = self._minimal_batch(prompt=prompt)
        batch_path = self._write_batch_fixture(batch_dict)
        batch = self.prompt_page_module.load_batch(batch_path)
        old_hash = batch.entries[0].prompt_hash
        self.assertEqual(old_hash, self._hash(prompt))
        mark_result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "mark",
                "--batch",
                str(batch_path),
                "--hash",
                old_hash,
                "--tested",
                "true",
                "--note",
                "checked",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(mark_result.returncode, 0)
        batch = self.prompt_page_module.load_batch(batch_path)
        self.assertTrue(batch.entries[0].tested)
        self.assertIsNotNone(batch.entries[0].tested_at)
        self.assertEqual(batch.entries[0].note, "checked")
        new_prompt = "Edited prompt text"
        new_hash = self._hash(new_prompt)
        batch_dict = self._minimal_batch(prompt=new_prompt)
        self._write_batch_fixture(batch_dict)
        batch_path.write_text(
            json.dumps(batch_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        mark_old_result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "mark",
                "--batch",
                str(batch_path),
                "--hash",
                old_hash,
                "--tested",
                "true",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(mark_old_result.returncode, 0)
        self.assertIn("no entry with prompt_hash", mark_old_result.stderr)
        mark_new_result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "mark",
                "--batch",
                str(batch_path),
                "--hash",
                new_hash,
                "--tested",
                "true",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(mark_new_result.returncode, 0)

    def test_mark_by_index_updates_tested_at(self) -> None:
        batch_dict = self._minimal_batch()
        batch_dict["entries"].append(
            {
                "index": 2,
                "anchor": "second entry",
                "kind": "generation",
                "type": "window-light-portrait",
                "profile": "natural-close-up",
                "prompt": "Another prompt",
                "prompt_hash": self._hash("Another prompt"),
                "reference": {"policy": "optional", "role": "likeness", "expected": False, "instruction": ""},
                "tested": False,
                "tested_at": None,
                "note": "",
            }
        )
        batch_path = self._write_batch_fixture(batch_dict)
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "mark",
                "--batch",
                str(batch_path),
                "--index",
                "1",
                "--tested",
                "true",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        batch = self.prompt_page_module.load_batch(batch_path)
        self.assertTrue(batch.entries[0].tested)
        self.assertIsNotNone(batch.entries[0].tested_at)
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "mark",
                "--batch",
                str(batch_path),
                "--index",
                "1",
                "--tested",
                "false",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        batch = self.prompt_page_module.load_batch(batch_path)
        self.assertFalse(batch.entries[0].tested)
        self.assertIsNone(batch.entries[0].tested_at)

    def test_mark_by_hash_works(self) -> None:
        prompt = "Test prompt for hash lookup"
        batch_dict = self._minimal_batch(prompt=prompt)
        batch_path = self._write_batch_fixture(batch_dict)
        prompt_hash = self._hash(prompt)
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "mark",
                "--batch",
                str(batch_path),
                "--hash",
                prompt_hash,
                "--tested",
                "true",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        batch = self.prompt_page_module.load_batch(batch_path)
        self.assertTrue(batch.entries[0].tested)
        self.assertIsNotNone(batch.entries[0].tested_at)

    def test_ingest_merge_rules(self) -> None:
        prompt_1 = "First prompt"
        prompt_2 = "Second prompt"
        batch_dict = self._minimal_batch(prompt=prompt_1)
        batch_dict["entries"].append(
            {
                "index": 2,
                "anchor": "second",
                "kind": "generation",
                "type": "window-light-portrait",
                "profile": "natural-close-up",
                "prompt": prompt_2,
                "prompt_hash": self._hash(prompt_2),
                "reference": {"policy": "optional", "role": "likeness", "expected": False, "instruction": ""},
                "tested": False,
                "tested_at": None,
                "note": "",
            }
        )
        batch_path = self._write_batch_fixture(batch_dict)
        hash_1 = self._hash(prompt_1)
        state_dict = {
            "schema": "zhiphoto-prompt-batch-state/v1",
            "batch_id": "prompts-test-batch-20260831T1200",
            "exported_at": "2026-08-31T16:00 (local)",
            "entries": [
                {"prompt_hash": hash_1, "tested": True, "tested_at": "2026-08-31T16:00 (local)", "note": "from export"},
                {"prompt_hash": "deadbeef", "tested": True, "tested_at": "2026-08-31T16:00 (local)", "note": "unmatched"},
            ],
        }
        state_path = self.temp_dir / "state.json"
        state_path.write_text(json.dumps(state_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "ingest",
                "--batch",
                str(batch_path),
                "--state",
                str(state_path),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        batch = self.prompt_page_module.load_batch(batch_path)
        self.assertTrue(batch.entries[0].tested)
        self.assertEqual(batch.entries[0].tested_at, "2026-08-31T16:00 (local)")
        self.assertEqual(batch.entries[0].note, "from export")
        self.assertFalse(batch.entries[1].tested)
        self.assertIsNone(batch.entries[1].tested_at)
        self.assertEqual(batch.entries[1].note, "")
        prompts_html = batch_path.parent / "prompts.html"
        self.assertTrue(prompts_html.exists())
        self.assertGreater(len(prompts_html.read_text()), 0)

    def test_html_escaping(self) -> None:
        prompt = 'Portrait test <script>alert(1)</script> with "quotes" & ampersands, 中文测试内容'
        batch_dict = self._minimal_batch(prompt=prompt)
        path = self._write_batch_fixture(batch_dict)
        batch = self.prompt_page_module.load_batch(path)
        html_text = self.prompt_page_module.render_html(batch)
        self.assertNotIn("<script>alert(1)</script>", html_text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_text)
        self.assertIn("&quot;quotes&quot;", html_text)
        self.assertIn("&amp;", html_text)
        self.assertIn("中文测试内容", html_text)


if __name__ == "__main__":
    unittest.main()
