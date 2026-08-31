from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import uuid
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SKILL = REPOSITORY_ROOT / "skills" / "zhiphoto"


class ImageCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture = Path(self.temporary_directory.name) / "zhiphoto"
        shutil.copytree(ACTIVE_SKILL, self.fixture)
        self.module_name = f"image_catalog_fixture_{uuid.uuid4().hex}"
        script = self.fixture / "scripts" / "image_catalog.py"
        spec = importlib.util.spec_from_file_location(self.module_name, script)
        if spec is None or spec.loader is None:
            self.fail("could not load copied image_catalog.py")
        self.catalog_module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_name] = self.catalog_module
        spec.loader.exec_module(self.catalog_module)

    def tearDown(self) -> None:
        sys.modules.pop(self.module_name, None)
        self.temporary_directory.cleanup()

    def replace_once(self, relative_path: str, old: str, new: str) -> None:
        path = self.fixture / relative_path
        content = path.read_text(encoding="utf-8")
        self.assertEqual(content.count(old), 1, f"fixture marker is not unique: {old!r}")
        path.write_text(content.replace(old, new, 1), encoding="utf-8")

    def assert_catalog_error(self, message_fragment: str) -> None:
        with self.assertRaises(self.catalog_module.CatalogError) as context:
            self.catalog_module.load_catalog()
        self.assertIn(message_fragment, str(context.exception))

    def test_active_catalog_and_cli_happy_paths(self) -> None:
        catalog = self.catalog_module.load_catalog()
        self.assertEqual(len(catalog.types), 10)
        self.assertEqual(len(catalog.profiles), 21)
        self.assertIn(
            ("08-selfie", "hyperreal-close-up"),
            {(profile.type, profile.id) for profile in catalog.profiles},
        )
        self.assertIn(
            ("02-window-light-portrait", "natural-close-up"),
            {(profile.type, profile.id) for profile in catalog.profiles},
        )
        self.assertIn("02-window-light-portrait", {image_type.id for image_type in catalog.types})
        self.assertIn(
            ("09-candid-car-flash-photo", "late-night-roadside-candid"),
            {(profile.type, profile.id) for profile in catalog.profiles},
        )
        self.assertIn("10-personal-ip", {image_type.id for image_type in catalog.types})
        self.assertEqual(
            {profile.id for profile in catalog.profiles if profile.type == "10-personal-ip"},
            {"canonical-mark", "character-sheet"},
        )
        self.assertEqual(sum(image_type.fallback for image_type in catalog.types), 1)
        self.assertFalse((self.fixture / "references" / "source-register.md").exists())

        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "list-types",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(completed.stdout)
        self.assertEqual(len(records), 10)
        self.assertEqual(sum(record["fallback"] for record in records), 1)

    def test_personal_ip_references_and_attribution_are_present(self) -> None:
        image_type = next(
            image_type for image_type in self.catalog_module.load_catalog().types
            if image_type.id == "10-personal-ip"
        )
        self.assertTrue(all(path.is_file() for path in image_type.required_ref_paths))
        type_root = ACTIVE_SKILL / "references" / "types" / "10-personal-ip"
        self.assertTrue((type_root / "LICENSE").is_file())
        self.assertIn("Copyright (c) 2026 s1dashu", (type_root / "LICENSE").read_text())
        foundation = (type_root / "foundations" / "identity-extraction.md").read_text()
        self.assertIn("reference photo", foundation)
        self.assertIn("age", foundation)
        self.assertIn("user's text", foundation)

        illustration_type = next(
            image_type for image_type in self.catalog_module.load_catalog().types
            if image_type.id == "03-article-illustration"
        )
        self.assertTrue(all(path.is_file() for path in illustration_type.required_ref_paths))
        self.assertIn(
            ("03-article-illustration", "article-illustration-series"),
            {(profile.type, profile.id) for profile in self.catalog_module.load_catalog().profiles},
        )
        illustration_root = ACTIVE_SKILL / "references" / "types" / "03-article-illustration"
        prompt_template = (
            illustration_root / "foundations" / "prompt-template.md"
        ).read_text(encoding="utf-8")
        personal_ip_reference = (
            illustration_root / "foundations" / "personal-ip-reference.md"
        ).read_text(encoding="utf-8")
        self.assertIn("ask the customer to attach it or point to a local file", prompt_template)
        self.assertIn("load it into context with `view_image`", prompt_template)
        self.assertIn("If multiple customer-explicit candidates could be the template", prompt_template)
        self.assertIn("load it into context with `view_image` if it is a local file", prompt_template)
        self.assertIn("Set `{PERSONAL_IP_BRANCH}` to exactly one of these prompt fragments", prompt_template)
        self.assertIn("Use the attached personal IP template as the recurring character reference.", prompt_template)
        self.assertIn("No personal IP template was supplied for this request.", prompt_template)
        self.assertIn("xiaohei-ip.md", prompt_template)
        self.assertIn("xiaohei-ip.md", "\n".join(str(path) for path in illustration_type.required_ref_paths))
        self.assertIn("this request", personal_ip_reference)
        self.assertIn("ask the customer to attach it or point to a local file", personal_ip_reference)
        self.assertIn("load it into context with `view_image`", personal_ip_reference)
        self.assertIn("If template intent exists and multiple candidate templates are plausible", personal_ip_reference)
        self.assertIn("If template intent exists", personal_ip_reference)
        self.assertIn("Do not fall back", personal_ip_reference)
        self.assertIn("use the original Xiaohei fallback", personal_ip_reference)
        self.assertNotIn(".local/personal-ip/", prompt_template)
        self.assertNotIn(".local/personal-ip/", personal_ip_reference)
        self.assertNotIn("exact local file path", personal_ip_reference)
        self.assertIn("customer's requested language", prompt_template)
        router = (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Default to single-image output", router)
        self.assertIn("If the user explicitly asks for `N` images, produce exactly `N` shots.", router)
        self.assertIn("If the user clearly wants multiple images but does not specify a count, ask for the count before generation.", router)
        self.assertIn("the agent handles the file directly as a Codex tool input", router)
        self.assertIn("ask the customer which one to use", router)
        self.assertIn("Select generation mode", router)
        self.assertIn("If multiple current-request attachments or described candidates could plausibly be the intended one, ask the customer which one to use", router)
        self.assertNotIn("Language gate", router)
        self.assertNotIn("customer's input language", router)
        self.assertNotIn("chinese-article-illustration", router)
        self.assertNotIn("jas-ip.png", prompt_template)
        self.assertNotIn("jas-ip.png", personal_ip_reference)
        self.assertFalse(
            (ACTIVE_SKILL / "references" / "types" / "chinese-article-illustration").exists()
        )
        active_xiaohei = (
            ACTIVE_SKILL
            / "references"
            / "types"
            / "03-article-illustration"
            / "foundations"
            / "xiaohei-ip.md"
        )
        self.assertTrue(active_xiaohei.is_file())
        type_notice = (illustration_root / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("falls back to Xiaohei only when the customer supplies no template at all", type_notice)
        self.assertNotIn("bundled example images", type_notice)
        style_dna = (illustration_root / "foundations" / "style-dna.md").read_text(encoding="utf-8")
        qa = (illustration_root / "foundations" / "qa-checklist.md").read_text(encoding="utf-8")
        series_profile = (
            illustration_root / "profiles" / "article-illustration-series.md"
        ).read_text(encoding="utf-8")
        single_profile = (
            illustration_root / "profiles" / "single-article-illustration.md"
        ).read_text(encoding="utf-8")
        type_doc = (illustration_root / "TYPE.md").read_text(encoding="utf-8")
        prompt_lines = prompt_template.splitlines()
        code_fence_start = prompt_lines.index("```text")
        code_fence_end = prompt_lines.index("```", code_fence_start + 1)
        prompt_body = "\n".join(prompt_lines[code_fence_start + 1 : code_fence_end])
        prompt_prelude = "\n".join(prompt_lines[:code_fence_start])
        self.assertIn("do not recolor", prompt_template)
        self.assertIn("to black", prompt_template)
        self.assertIn("Use the recurring character's own signature palette", style_dna)
        self.assertIn("lost its signature palette/style", qa)
        self.assertIn("full article or long post by itself does not trigger this profile", series_profile)
        self.assertIn("This remains the default even when the source material is a full article or long post", single_profile)
        self.assertIn("Use `single-article-illustration` by default, including when the source material is a full article or long post", type_doc)
        self.assertIn("using the customer's recurring personal-IP template when supplied and Xiaohei otherwise", single_profile)
        self.assertIn("customer's recurring personal IP or the Xiaohei fallback", series_profile)
        self.assertIn("{PERSONAL_IP_BRANCH}", prompt_body)
        self.assertNotIn("If a customer-explicit template was attached or designated for this request", prompt_body)
        self.assertNotIn("If no customer-explicit template was supplied at all", prompt_body)
        self.assertNotIn("Do not inspect workspace-local images", prompt_body)
        self.assertIn("ask the customer to attach it or point to a local file", prompt_prelude)
        self.assertNotIn("exact designated local path", prompt_prelude)

    def test_transport_codex_image_gen(self) -> None:
        """Codex image_gen transport documents image generation through Codex's built-in tool."""
        codex_gen = (
            ACTIVE_SKILL / "references" / "transport" / "codex-image-gen.md"
        ).read_text(encoding="utf-8")
        # Core workflow: use Codex's built-in image_gen, not browser
        self.assertIn("built-in `image_gen` tool", codex_gen)
        self.assertIn("This is a first-party Codex tool call", codex_gen)
        self.assertIn("no browser, no", codex_gen)
        self.assertIn("no chatgpt.com", codex_gen)
        # Reference/edit-target handling via view_image
        self.assertIn("Obtain the file", codex_gen)
        self.assertIn("A local file must go through `view_image`", codex_gen)
        # Pre-generation confirmation gate
        self.assertIn("pre-generation confirmation gate", codex_gen)
        self.assertIn("Apply this gate once per `image_gen` call", codex_gen)
        # Decision point: convert to prompt-handoff transport
        self.assertIn("prompt-handoff transport", codex_gen)
        self.assertIn("references/transport/prompt-handoff.md", codex_gen)
        # Excluded: browser-era terms
        self.assertNotIn("pageAssets", codex_gen)
        self.assertNotIn("Codex Browser", codex_gen)
        self.assertNotIn("Host detection", codex_gen)

    def test_transport_prompt_handoff(self) -> None:
        """Prompt-handoff transport composes prompts in batch.json without calling image_gen."""
        prompt_handoff = (
            ACTIVE_SKILL / "references" / "transport" / "prompt-handoff.md"
        ).read_text(encoding="utf-8")
        # Core concept: hand off prompts to human, no image generation
        self.assertIn("composing a batch of one or more prompts", prompt_handoff)
        self.assertIn("self-contained web page for a human to run themselves", prompt_handoff)
        self.assertIn("never calls `image_gen`", prompt_handoff)
        # batch.json schema and contract
        self.assertIn("batch.json", prompt_handoff)
        self.assertIn("zhiphoto-prompt-batch/v1", prompt_handoff)
        # Reference-indicator derivation
        self.assertIn("Reference-indicator derivation", prompt_handoff)
        self.assertIn("expected", prompt_handoff)
        # No automation guardrails
        self.assertIn("Never open, navigate to, link to, script, or submit anything to chatgpt.com", prompt_handoff)
        # Invoke prompt_page.py
        self.assertIn("prompt_page.py render", prompt_handoff)
        # Excluded: browser/website automation
        self.assertNotIn("auto-navigation to chatgpt.com", prompt_handoff)
        self.assertNotIn("chatgpt.com and fetch", prompt_handoff)

    def test_skill_md_generation_mode_lanes(self) -> None:
        """SKILL.md Select generation mode section documents three routing lanes."""
        skill_md = (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        # Section exists
        self.assertIn("## Select generation mode", skill_md)
        # Three lanes documented
        self.assertIn("**(P) Prompt handoff**", skill_md)
        self.assertIn("**(A) Auto-generate**", skill_md)
        self.assertIn("**(G) Ask-then-generate**", skill_md)
        # Lane P: deliverable is prompts
        self.assertIn("the request's deliverable is *prompts*", skill_md)
        self.assertIn("generate 10 prompts", skill_md)
        self.assertIn("Continue to **Compose, present, and record**", skill_md)
        # Lane A: generate directly
        self.assertIn("explicitly says to generate directly", skill_md)
        self.assertIn("generate the image directly", skill_md)
        # Lane G: default ask-then-generate
        self.assertIn("the default when neither of the above matches", skill_md)
        # Disambiguation question
        self.assertIn("images generated here, or prompts for you to run yourself?", skill_md)
        # Count rules
        self.assertIn("lane P reuses the exact count logic", skill_md)
        # References to transport files
        self.assertIn("references/transport/prompt-handoff.md", skill_md)
        self.assertIn("references/transport/codex-image-gen.md", skill_md)

    def test_agents_openai_metadata_contract(self) -> None:
        """Verify agents/openai.yaml contains engine contract fields and covers modification."""
        openai_yaml = (
            ACTIVE_SKILL / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        # Contract fields must be present
        self.assertIn("short_description", openai_yaml)
        self.assertIn("default_prompt", openai_yaml)
        # Modification must be covered (not just generation)
        self.assertIn("modify", openai_yaml)

    def test_new_type_is_discovered_without_router_or_script_changes(self) -> None:
        router_before = (self.fixture / "SKILL.md").read_bytes()
        script_path = self.fixture / "scripts" / "image_catalog.py"
        script_before = script_path.read_bytes()
        type_directory = self.fixture / "references" / "types" / "poster"
        (type_directory / "foundations").mkdir(parents=True)
        (type_directory / "profiles").mkdir()
        (type_directory / "foundations" / "layout.md").write_text(
            "# Poster Layout\n\nKeep hierarchy legible.\n", encoding="utf-8"
        )
        (type_directory / "TYPE.md").write_text(
            textwrap.dedent(
                """\
                ---
                schema: image-type/v2
                type_version: 1
                id: poster
                title: Poster
                summary: Designed poster images with intentional hierarchy and graphic layout.
                keywords: ["poster", "graphic layout"]
                profile_kind: format
                fallback: false
                required_refs: ["references/types/poster/foundations/layout.md"]
                category: general
                reference_policy: optional
                reference_role: likeness
                sort_order: 50
                ---

                # Poster
                """
            ),
            encoding="utf-8",
        )
        (type_directory / "profiles" / "editorial.md").write_text(
            textwrap.dedent(
                """\
                ---
                schema: image-profile/v1
                profile_version: 1
                id: editorial
                type: poster
                kind: format
                title: Editorial Poster
                summary: Typographic editorial poster with a strong information hierarchy.
                keywords: ["editorial", "typography"]
                maturity: general
                adult_only: false
                sort_order: 10
                ---

                # Editorial Poster
                """
            ),
            encoding="utf-8",
        )

        catalog = self.catalog_module.load_catalog()
        self.assertIn("poster", {image_type.id for image_type in catalog.types})
        self.assertIn(
            ("poster", "editorial"),
            {(profile.type, profile.id) for profile in catalog.profiles},
        )
        self.assertEqual(router_before, (self.fixture / "SKILL.md").read_bytes())
        self.assertEqual(script_before, script_path.read_bytes())

    def test_rejects_more_than_one_fallback(self) -> None:
        self.replace_once(
            "references/types/08-selfie/TYPE.md", "fallback: false", "fallback: true"
        )
        self.assert_catalog_error("exactly one fallback type")

    def test_rejects_unsafe_required_reference(self) -> None:
        self.replace_once(
            "references/types/01-general/TYPE.md",
            'required_refs: ["references/types/01-general/foundations/direct-prompt.md"]',
            'required_refs: ["../outside.md"]',
        )
        self.assert_catalog_error("unsafe required_refs path")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_rejects_required_reference_symlink_escape(self) -> None:
        outside = Path(self.temporary_directory.name) / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        link = self.fixture / "references" / "types" / "01-general" / "foundations" / "escape.md"
        link.symlink_to(outside)
        self.replace_once(
            "references/types/01-general/TYPE.md",
            'required_refs: ["references/types/01-general/foundations/direct-prompt.md"]',
            'required_refs: ["references/types/01-general/foundations/escape.md"]',
        )
        self.assert_catalog_error("symlink escapes its type folder")

    def test_rejects_type_folder_id_mismatch(self) -> None:
        self.replace_once("references/types/01-general/TYPE.md", "id: 01-general", "id: other")
        self.assert_catalog_error("containing folder must match type id")

    def test_rejects_profile_kind_mismatch(self) -> None:
        self.replace_once(
            "references/types/01-general/profiles/direct.md", "kind: mode", "kind: scene"
        )
        self.assert_catalog_error("must match type profile_kind")

    def test_rejects_inconsistent_adult_only_flag(self) -> None:
        self.replace_once(
            "references/types/08-selfie/profiles/adult-sensual-glamour.md",
            "adult_only: true",
            "adult_only: false",
        )
        self.assert_catalog_error("requires adult_only: true")

    def test_rejects_duplicate_profile_id_within_type(self) -> None:
        original = self.fixture / "references" / "types" / "08-selfie" / "profiles" / "casual-sns.md"
        duplicate_directory = original.parent / "nested"
        duplicate_directory.mkdir()
        shutil.copy2(original, duplicate_directory / original.name)
        self.assert_catalog_error("duplicate profile ids within types")

    def test_sort_order_ties_use_id_as_deterministic_tiebreaker(self) -> None:
        self.replace_once(
            "references/types/08-selfie/profiles/outdoor-place-daylight.md",
            "sort_order: 20",
            "sort_order: 10",
        )
        catalog = self.catalog_module.load_catalog()
        tied = [
            profile.id
            for profile in catalog.profiles
            if profile.type == "08-selfie" and profile.sort_order == 10
        ]
        self.assertEqual(tied, sorted(tied))
        self.assertEqual(tied, ["casual-sns", "outdoor-place-daylight"])

    def test_list_types_includes_category_reference_policy_reference_role(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "list-types",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(completed.stdout)
        self.assertEqual(len(records), 10)
        # Check all records have required fields
        for record in records:
            self.assertIn("category", record)
            self.assertIn("reference_policy", record)
            self.assertIn("reference_role", record)

        # Check category mappings
        category_map = {record["id"]: record["category"] for record in records}
        self.assertEqual(category_map["01-general"], "general")
        self.assertEqual(category_map["03-article-illustration"], "illustration")
        for type_id in ["08-selfie", "11-realistic-human-photo", "02-window-light-portrait", "09-candid-car-flash-photo", "10-personal-ip"]:
            self.assertEqual(category_map[type_id], "portrait")

    def test_list_types_grouped_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "list-types",
                "--grouped",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(completed.stdout)
        # Should be a dict with category keys
        self.assertIsInstance(records, dict)
        # Should have exactly three categories
        self.assertEqual(set(records.keys()), {"general", "illustration", "portrait"})
        # Check counts
        self.assertEqual(len(records["general"]), 3)
        self.assertEqual(len(records["illustration"]), 2)
        self.assertEqual(len(records["portrait"]), 5)

    def test_type_sort_order_unique_across_catalog(self) -> None:
        catalog = self.catalog_module.load_catalog()
        sort_orders = [image_type.sort_order for image_type in catalog.types]
        # Check all sort_order values are unique
        self.assertEqual(len(sort_orders), len(set(sort_orders)))

    def test_route_chinese_query_without_reference(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "深夜车里帮我拍一张",
                "--has-reference",
                "no",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        # Top candidate should be candid-car-flash-photo
        self.assertEqual(results[0]["type"], "09-candid-car-flash-photo")
        # personal-ip should NOT be the leader
        top_type = results[0]["type"]
        self.assertNotEqual(top_type, "10-personal-ip")

    def test_route_english_query_with_reference(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "make my IP character sheet",
                "--has-reference",
                "yes",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        # Top candidate should be personal-ip
        self.assertEqual(results[0]["type"], "10-personal-ip")

    def test_validate_rejects_v1_schema(self) -> None:
        self.replace_once(
            "references/types/08-selfie/TYPE.md",
            "schema: image-type/v2",
            "schema: image-type/v1",
        )
        self.assert_catalog_error("schema 'image-type/v1' is no longer supported")

    def test_validate_rejects_missing_category(self) -> None:
        # Read the TYPE.md, remove the category line, write it back
        type_md = self.fixture / "references" / "types" / "08-selfie" / "TYPE.md"
        content = type_md.read_text(encoding="utf-8")
        # Remove the category line
        lines = content.split("\n")
        lines = [line for line in lines if not line.startswith("category:")]
        type_md.write_text("\n".join(lines), encoding="utf-8")
        self.assert_catalog_error("missing ['category']")

    def test_personal_ip_produces_identity_template(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "list-types",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(completed.stdout)
        personal_ip = next((r for r in records if r["id"] == "10-personal-ip"), None)
        self.assertIsNotNone(personal_ip)
        self.assertEqual(personal_ip.get("produces"), "identity-template")

    def test_article_illustration_consumes_identity_template(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "list-types",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(completed.stdout)
        article_illustration = next((r for r in records if r["id"] == "03-article-illustration"), None)
        self.assertIsNotNone(article_illustration)
        self.assertEqual(article_illustration.get("consumes"), "identity-template")

    def test_route_late_night_candid_photo_in_car(self) -> None:
        """Phase 1 fix cycle 1: route leader test for previously-failing English brief."""
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "late-night candid photo inside a car",
                "--has-reference",
                "no",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        # Leader should be candid-car-flash-photo
        self.assertEqual(results[0]["type"], "09-candid-car-flash-photo")

    def test_route_natural_window_light_portrait(self) -> None:
        """Phase 1 fix cycle 1: route leader test for previously-failing English brief."""
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "natural window-light close-up portrait",
                "--has-reference",
                "no",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        # Leader should be window-light-portrait
        self.assertEqual(results[0]["type"], "02-window-light-portrait")

    def test_route_hyperreal_realistic_face_portrait(self) -> None:
        """Phase 1 fix cycle 1: route leader test for previously-failing English brief."""
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "hyperreal realistic face portrait",
                "--has-reference",
                "no",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        # Leader should be realistic-human-photo
        self.assertEqual(results[0]["type"], "11-realistic-human-photo")

    def test_route_ip_based_post_cover_non_regression_with_new_type(self) -> None:
        """Additive-constraint non-regression: adding image-to-post-cover must not
        change ip-based-post-cover's existing lead for its own established brief."""
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "用我的角色参考图给这期视频做一张小红书封面",
                "--has-reference",
                "yes",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "05-ip-based-post-cover")

    def test_route_image_to_post_cover_leads_for_screenshot_brief(self) -> None:
        """image-to-post-cover must decisively LEAD the shortlist for a brief naming
        its discriminating from-image vocabulary (截图/图里的字/图里的话/文字/提取).

        Fix cycle 1 (2026-08-29): the original keyword lists left every Chinese
        keyword of both this type and ip-based-post-cover ending in the shared
        suffix 封面, so any 封面-brief bigram-matched every keyword of both types
        equally and ip-based-post-cover's larger profile-keyword volume (two
        profiles vs. this type's one) won on raw match count. The fix added
        封面-free, screenshot/extraction-specific keywords (截图里的文字/截图里的字/
        截图里的话/提取截图文字/截图文字 plus an English partial-match set) that
        match this brief's actual discriminating vocabulary but do NOT match
        ip-based-post-cover's character/episode briefs, since those briefs contain
        no 截图/图里/提取/文字 substrings. See
        test_route_ip_based_post_cover_non_regression_with_new_type above for the
        matching non-regression check.
        """
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "把这张截图里的字做成小红书封面",
                "--has-reference",
                "yes",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0]["type"], "06-image-to-post-cover")
        # Decisive lead: comfortably ahead of the runner-up, not a razor-thin tie.
        self.assertGreater(results[0]["score"], results[1]["score"] + 10)
        self.assertIn("截图里的字", results[0]["matched_terms"])

    def test_route_image_to_post_cover_leads_for_english_screenshot_brief(self) -> None:
        """The English partial-match keywords added in fix cycle 1 (screenshot words
        cover / words in screenshot / turn screenshot into cover / xiaohongshu
        cover) must let image-to-post-cover lead an English screenshot-to-cover
        brief, where none of the Chinese-keyword bigram machinery applies."""
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                "turn the words in this screenshot into a xiaohongshu cover",
                "--has-reference",
                "yes",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        results = json.loads(completed.stdout)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "06-image-to-post-cover")

    def _route(self, brief: str, has_reference: str) -> list[dict]:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "route",
                "--brief",
                brief,
                "--has-reference",
                has_reference,
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_route_matrix_image_to_post_cover_still_leads(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 1: adding image-to-image must
        not disturb image-to-post-cover's existing lead for its own brief."""
        results = self._route("把这张截图里的字做成小红书封面", "yes")
        self.assertEqual(results[0]["type"], "06-image-to-post-cover")

    def test_route_matrix_ip_based_post_cover_still_leads(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 2: non-regression."""
        results = self._route(
            "用我的角色参考图给这期视频做一张小红书封面。这期一句话："
            "独立开发者用 skill 把周更从熬夜改成定时发出去",
            "yes",
        )
        self.assertEqual(results[0]["type"], "05-ip-based-post-cover")

    def test_route_matrix_image_to_image_leads_plain_reference_brief(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 3: 照这张图再画一张."""
        results = self._route("照这张图再画一张", "yes")
        self.assertEqual(results[0]["type"], "07-image-to-image")

    def test_route_matrix_image_to_image_style_transfer_leads(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 4: 风格迁移 brief selects
        style-transfer specifically."""
        results = self._route("风格迁移：用这张图的风格画一只猫", "yes")
        self.assertEqual(results[0]["type"], "07-image-to-image")
        self.assertEqual(results[0]["profile"], "style-transfer")

    def test_route_matrix_image_to_image_similar_leads_english_brief(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 5: English brief selects
        similar specifically."""
        results = self._route("make one like this image", "yes")
        self.assertEqual(results[0]["type"], "07-image-to-image")
        self.assertEqual(results[0]["profile"], "similar")

    def test_route_matrix_image_to_image_restyle_leads_watercolor_brief(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 6: 把这张照片变成水彩风
        (the edit-vs-reference question may fire first per the design doc §4;
        this only checks routing, not that fork)."""
        results = self._route("把这张照片变成水彩风", "yes")
        self.assertEqual(results[0]["type"], "07-image-to-image")
        self.assertEqual(results[0]["profile"], "restyle")

    def test_route_matrix_image_to_image_silent_on_likeness_selfie_brief(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 7 (partial coverage): the
        keyword discipline (no 自拍/selfie/portrait vocabulary) must keep
        image-to-image out of this likeness brief's shortlist entirely — proves the
        '一张' generic-bigram fix (2026-08-30 fix cycle) holds. This does NOT assert
        `selfie` leads: `selfie`'s own keyword list has no Chinese phrases at all, so
        it scores 0 on any Chinese-only brief and is already crowded out of the
        top-5 shortlist by every `required`-policy type's has-reference bonus alone
        — a pre-existing gap in `selfie`'s keywords, not something image-to-image
        caused, and out of this task's authorized scope to fix (see the task
        report)."""
        results = self._route("在海边拍一张自拍，用我附的照片保持长相", "yes")
        types_present = {candidate["type"] for candidate in results}
        self.assertNotIn("07-image-to-image", types_present)

    def test_route_matrix_article_illustration_still_leads_no_reference(self) -> None:
        """2026-08-30 image-to-image brief matrix, row 8 (eval-03 brief,
        has-reference no): non-regression. This was broken by the original
        design-doc keyword '照这张图再画一张' (bigram '一张' matched '...配一张插图')
        before the 2026-08-30 fix cycle keyword correction."""
        results = self._route(
            "给一篇讲\"小习惯每天积累,最后变成大结果\"的文章配一张插图。", "no"
        )
        self.assertEqual(results[0]["type"], "03-article-illustration")

    def test_route_list_profiles_image_to_image_order(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(self.fixture / "scripts" / "image_catalog.py"),
                "list-profiles",
                "--type",
                "07-image-to-image",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        records = json.loads(completed.stdout)
        self.assertEqual(
            [record["id"] for record in records],
            ["restyle", "recreate", "style-transfer", "similar"],
        )
        for record in records:
            self.assertEqual(record["type"], "07-image-to-image")
            self.assertEqual(record["kind"], "usage")

    def test_resolve_image_to_image_profiles_carry_visual_source_role(self) -> None:
        for profile_id in ("restyle", "recreate", "style-transfer", "similar"):
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self.fixture / "scripts" / "image_catalog.py"),
                    "resolve",
                    "--type",
                    "07-image-to-image",
                    "--profile",
                    profile_id,
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["type"]["reference_policy"], "required")
            self.assertEqual(result["type"]["reference_role"], "visual-source")
            self.assertEqual(result["profile"]["id"], profile_id)

    def test_skill_md_contains_no_type_ids(self) -> None:
        """SKILL.md must not hard-code any catalog type IDs."""
        skill_md = (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        # Check that none of the seven type IDs appear in SKILL.md
        type_ids = ["selfie", "candid-car", "window-light", "realistic-human", "article-illustration", "personal-ip"]
        for type_id in type_ids:
            self.assertNotIn(type_id, skill_md, f"SKILL.md should not contain type ID '{type_id}'")

    def test_skill_md_references_route_command(self) -> None:
        """SKILL.md must reference the route command."""
        skill_md = (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("route --brief", skill_md, "SKILL.md should reference 'route --brief' command")

    def test_skill_md_modification_delta_contract(self) -> None:
        """SKILL.md must contain the modification delta contract phrase."""
        skill_md = (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("change only", skill_md, "SKILL.md should contain modification delta contract: 'change only'")
        self.assertIn("keep everything else identical", skill_md, "SKILL.md should contain: 'keep everything else identical'")


if __name__ == "__main__":
    unittest.main()
