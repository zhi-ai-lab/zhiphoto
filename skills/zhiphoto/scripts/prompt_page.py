#!/usr/bin/env python3
"""Render, mark, and ingest tested state for zhiphoto prompt-handoff batches."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


BATCH_SCHEMA = "zhiphoto-prompt-batch/v1"
STATE_SCHEMA = "zhiphoto-prompt-batch-state/v1"

BATCH_REQUIRED_KEYS = {"schema", "batch_id", "created_at", "brief", "entries"}
ENTRY_REQUIRED_KEYS = {
    "index",
    "anchor",
    "kind",
    "type",
    "profile",
    "prompt",
    "prompt_hash",
    "reference",
    "tested",
    "tested_at",
    "note",
}
REFERENCE_REQUIRED_KEYS = {"policy", "role", "expected", "instruction"}

KIND_VALUES = {"generation", "modification"}
REFERENCE_POLICY_VALUES = {"required", "optional"}

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BATCH_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
PROMPT_HASH_PATTERN = re.compile(r"^[0-9a-f]{8}$")


class PromptPageError(ValueError):
    """A batch.json manifest or exported state file is malformed, or a lookup failed."""


@dataclass
class ReferenceInfo:
    policy: str
    role: str
    expected: bool
    instruction: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "role": self.role,
            "expected": self.expected,
            "instruction": self.instruction,
        }


@dataclass
class BatchEntry:
    index: int
    anchor: str
    kind: str
    type: str
    profile: str
    prompt: str
    prompt_hash: str
    reference: ReferenceInfo
    tested: bool
    tested_at: str | None
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "anchor": self.anchor,
            "kind": self.kind,
            "type": self.type,
            "profile": self.profile,
            "prompt": self.prompt,
            "prompt_hash": self.prompt_hash,
            "reference": self.reference.to_dict(),
            "tested": self.tested,
            "tested_at": self.tested_at,
            "note": self.note,
        }


@dataclass
class Batch:
    schema: str
    batch_id: str
    created_at: str
    brief: str
    entries: list[BatchEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "brief": self.brief,
            "entries": [entry.to_dict() for entry in self.entries],
        }


# ---------------------------------------------------------------------------
# Validation helpers (mirror image_catalog.py's fail-loud, name-what's-wrong style).
# Unlike image_catalog.py's frontmatter parser, values here come pre-typed from
# json.load, and string fields are never stripped: a prompt's exact bytes are what
# prompt_hash is computed over and what "tested" attests to, so trimming whitespace
# would silently change meaning.
# ---------------------------------------------------------------------------


def _strict_keys(mapping: Any, required: set[str], label: str, path: Path) -> None:
    if not isinstance(mapping, dict):
        raise PromptPageError(f"{path}: {label} must be a JSON object")
    actual = set(mapping)
    if actual == required:
        return
    details = []
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing:
        details.append(f"missing {missing}")
    if extra:
        details.append(f"unknown {extra}")
    raise PromptPageError(f"{path}: strict {label} schema violation: {', '.join(details)}")


def _string_field(mapping: dict[str, Any], key: str, label: str, path: Path, *, allow_empty: bool = False) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise PromptPageError(f"{path}: {label}.{key} must be a string")
    if not allow_empty and not value.strip():
        raise PromptPageError(f"{path}: {label}.{key} must be a non-empty string")
    return value


def _bool_field(mapping: dict[str, Any], key: str, label: str, path: Path) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise PromptPageError(f"{path}: {label}.{key} must be the JSON boolean true or false")
    return value


def _positive_int_field(mapping: dict[str, Any], key: str, label: str, path: Path) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise PromptPageError(f"{path}: {label}.{key} must be a positive integer")
    return value


def _enum_field(mapping: dict[str, Any], key: str, allowed: set[str], label: str, path: Path) -> str:
    value = _string_field(mapping, key, label, path)
    if value not in allowed:
        raise PromptPageError(f"{path}: {label}.{key} must be one of {sorted(allowed)}")
    return value


def _slug_field(mapping: dict[str, Any], key: str, label: str, path: Path) -> str:
    value = _string_field(mapping, key, label, path)
    if not SLUG_PATTERN.fullmatch(value):
        raise PromptPageError(f"{path}: {label}.{key} must be a lowercase hyphenated slug")
    return value


def _batch_id_field(mapping: dict[str, Any], path: Path) -> str:
    value = _string_field(mapping, "batch_id", "batch.json", path)
    if not BATCH_ID_PATTERN.fullmatch(value):
        raise PromptPageError(
            f"{path}: batch_id must match {BATCH_ID_PATTERN.pattern!r} "
            "(it doubles as a localStorage key segment and a download filename)"
        )
    return value


def _prompt_hash_field(mapping: dict[str, Any], prompt: str, label: str, path: Path) -> str:
    value = mapping.get("prompt_hash")
    if not isinstance(value, str) or not PROMPT_HASH_PATTERN.fullmatch(value):
        raise PromptPageError(f"{path}: {label}.prompt_hash must be an 8-character lowercase hex string")
    # Design choice (documented per the task's "pick one" instruction): prompt_hash is
    # ALWAYS verified against the current prompt text and rejected loudly on mismatch,
    # never silently recomputed. A "tested" mark attests to exact prompt text (decision 7
    # in the design doc), so a stale/wrong hash is treated as a corrupt manifest -- the
    # same fail-loud posture image_catalog.py takes for every other consistency check
    # (e.g. maturity/adult_only). This also means edit-invalidation works automatically:
    # whoever edits `prompt` must also recompute `prompt_hash`, which naturally produces
    # a new localStorage/ingest key and drops the old "tested" mark.
    expected = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
    if value != expected:
        raise PromptPageError(
            f"{path}: {label}.prompt_hash {value!r} does not match sha256(prompt)[:8] "
            f"{expected!r}; recompute prompt_hash after editing prompt"
        )
    return value


def _tested_at_field(mapping: dict[str, Any], tested: bool, label: str, path: Path) -> str | None:
    value = mapping.get("tested_at")
    if tested:
        if not isinstance(value, str) or not value.strip():
            raise PromptPageError(f"{path}: {label}.tested_at must be a non-empty string when tested is true")
        return value
    if value is not None:
        raise PromptPageError(f"{path}: {label}.tested_at must be null when tested is false")
    return None


def _load_reference(raw: Any, *, label: str, path: Path) -> ReferenceInfo:
    ref_label = f"{label}.reference"
    _strict_keys(raw, REFERENCE_REQUIRED_KEYS, ref_label, path)
    policy = _enum_field(raw, "policy", REFERENCE_POLICY_VALUES, ref_label, path)
    role = _slug_field(raw, "role", ref_label, path)
    expected = _bool_field(raw, "expected", ref_label, path)
    instruction = _string_field(raw, "instruction", ref_label, path, allow_empty=not expected)
    if expected and not instruction.strip():
        raise PromptPageError(f"{path}: {ref_label}.instruction must be non-empty when expected is true")
    return ReferenceInfo(policy=policy, role=role, expected=expected, instruction=instruction)


def _load_entry(raw: Any, *, position: int, path: Path) -> BatchEntry:
    label = f"entries[{position}]"
    if not isinstance(raw, dict):
        raise PromptPageError(f"{path}: {label} must be a JSON object")
    _strict_keys(raw, ENTRY_REQUIRED_KEYS, label, path)
    entry_index = _positive_int_field(raw, "index", label, path)
    anchor = _string_field(raw, "anchor", label, path)
    kind = _enum_field(raw, "kind", KIND_VALUES, label, path)
    entry_type = _slug_field(raw, "type", label, path)
    profile = _slug_field(raw, "profile", label, path)
    prompt = _string_field(raw, "prompt", label, path)
    prompt_hash = _prompt_hash_field(raw, prompt, label, path)
    reference = _load_reference(raw["reference"], label=label, path=path)
    tested = _bool_field(raw, "tested", label, path)
    tested_at = _tested_at_field(raw, tested, label, path)
    note = _string_field(raw, "note", label, path, allow_empty=True)
    return BatchEntry(
        index=entry_index,
        anchor=anchor,
        kind=kind,
        type=entry_type,
        profile=profile,
        prompt=prompt,
        prompt_hash=prompt_hash,
        reference=reference,
        tested=tested,
        tested_at=tested_at,
        note=note,
    )


def _check_unique(values: list[Any], noun: str, path: Path) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise PromptPageError(f"{path}: duplicate {noun}: {duplicates}")


def load_batch(path: Path) -> Batch:
    if not path.is_file():
        raise PromptPageError(f"{path}: batch file not found")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PromptPageError(f"{path}: could not read batch file: {exc}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise PromptPageError(f"{path}: invalid JSON: {exc}") from exc
    _strict_keys(data, BATCH_REQUIRED_KEYS, "batch.json", path)
    schema = _string_field(data, "schema", "batch.json", path)
    if schema != BATCH_SCHEMA:
        raise PromptPageError(f"{path}: schema must be exactly {BATCH_SCHEMA!r}, found {schema!r}")
    batch_id = _batch_id_field(data, path)
    created_at = _string_field(data, "created_at", "batch.json", path)
    brief = _string_field(data, "brief", "batch.json", path)
    raw_entries = data["entries"]
    if not isinstance(raw_entries, list) or not raw_entries:
        raise PromptPageError(f"{path}: 'entries' must be a non-empty JSON array")
    entries = [
        _load_entry(raw_entry, position=position, path=path)
        for position, raw_entry in enumerate(raw_entries, start=1)
    ]
    _check_unique([entry.index for entry in entries], "entry indices", path)
    _check_unique([entry.prompt_hash for entry in entries], "entry prompt_hash values", path)
    return Batch(schema=schema, batch_id=batch_id, created_at=created_at, brief=brief, entries=entries)


def save_batch(batch: Batch, path: Path) -> None:
    path.write_text(json.dumps(batch.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_state(path: Path) -> dict[str, Any]:
    """Load an exported tested-state file (the shape the page's "Export tested state"
    button produces). Deliberately more lenient than load_batch's strict-key policing:
    batch.json is the authoritative record and must be exactly right, but a state file
    is an interchange blob -- it may also be hand-written when Jason just tells the
    agent which indexes passed -- so only the fields ingest actually needs are checked.
    """
    if not path.is_file():
        raise PromptPageError(f"{path}: state file not found")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PromptPageError(f"{path}: could not read state file: {exc}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise PromptPageError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PromptPageError(f"{path}: state file must contain a JSON object")
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        raise PromptPageError(f"{path}: state file must contain an 'entries' array")
    entries: list[dict[str, Any]] = []
    for position, raw_entry in enumerate(raw_entries, start=1):
        label = f"state entries[{position}]"
        if not isinstance(raw_entry, dict):
            raise PromptPageError(f"{path}: {label} must be a JSON object")
        prompt_hash = raw_entry.get("prompt_hash")
        if not isinstance(prompt_hash, str) or not PROMPT_HASH_PATTERN.fullmatch(prompt_hash):
            raise PromptPageError(f"{path}: {label}.prompt_hash must be an 8-character lowercase hex string")
        tested = raw_entry.get("tested")
        if not isinstance(tested, bool):
            raise PromptPageError(f"{path}: {label}.tested must be a boolean")
        tested_at = raw_entry.get("tested_at")
        if tested_at is not None and not isinstance(tested_at, str):
            raise PromptPageError(f"{path}: {label}.tested_at must be a string or null")
        note = raw_entry.get("note", "")
        if not isinstance(note, str):
            raise PromptPageError(f"{path}: {label}.note must be a string")
        entries.append({"prompt_hash": prompt_hash, "tested": tested, "tested_at": tested_at, "note": note})
    return {"entries": entries}


# ---------------------------------------------------------------------------
# Deterministic HTML rendering. _STYLE and _SCRIPT are static (no interpolation), and
# every dynamic fragment is built from `batch` alone with no wall-clock/random content,
# so render_html(batch) is byte-identical across runs for the same batch.json.
# ---------------------------------------------------------------------------

_STYLE = """
:root {
  color-scheme: light dark;
  --bg: #f7f7f5;
  --surface: #ffffff;
  --text: #17181c;
  --muted: #5b5f6b;
  --border: #dcdcd7;
  --accent: #2563eb;
  --accent-contrast: #ffffff;
  --badge-required-bg: #fff4e5;
  --badge-required-border: #f0b429;
  --badge-required-text: #8a5a00;
  --badge-optional-bg: #eef7ee;
  --badge-optional-border: #7bc47f;
  --badge-optional-text: #2f6b30;
  --chip-bg: #eef0f4;
  --chip-text: #33384a;
  --code-bg: #f4f4f2;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14151a;
    --surface: #1d1f26;
    --text: #f1f1ef;
    --muted: #a9acb8;
    --border: #33353f;
    --accent: #7da2f5;
    --accent-contrast: #0b0d12;
    --badge-required-bg: #3a2c10;
    --badge-required-border: #caa23a;
    --badge-required-text: #f2cf83;
    --badge-optional-bg: #16321a;
    --badge-optional-border: #4f8f52;
    --badge-optional-text: #9fe3a2;
    --chip-bg: #262933;
    --chip-text: #c7cbe0;
    --code-bg: #14161c;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.5;
}
.page { max-width: 820px; margin: 0 auto; padding: 32px 20px 64px; }
.page-head h1 { margin: 0 0 8px; font-size: 1.5rem; }
.brief { margin: 0 0 8px; }
.meta { margin: 0 0 8px; color: var(--muted); font-size: 0.9rem; }
.reminder { margin: 0 0 24px; color: var(--muted); font-size: 0.85rem; }
.entries { display: flex; flex-direction: column; gap: 20px; }
.entry {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
}
.entry-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 8px; }
.entry-head h2 { margin: 0; font-size: 1.05rem; }
.ordinal { color: var(--muted); margin-right: 6px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  background: var(--chip-bg);
  color: var(--chip-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.75rem;
  white-space: nowrap;
}
.badge {
  display: inline-block;
  margin: 10px 0;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  border: 1px solid transparent;
}
.badge-optional {
  background: var(--badge-optional-bg);
  border-color: var(--badge-optional-border);
  color: var(--badge-optional-text);
}
.badge-required {
  background: var(--badge-required-bg);
  border-color: var(--badge-required-border);
  color: var(--badge-required-text);
}
.prompt-block { margin: 10px 0; }
.prompt-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.hash { color: var(--muted); font-size: 0.75rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.copy-button, #export-state {
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.85rem;
  cursor: pointer;
}
.copy-button:hover, #export-state:hover { opacity: 0.9; }
.prompt-text {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85rem;
}
.tested-row { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-top: 10px; }
.tested-toggle { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; }
.timestamp { color: var(--muted); font-size: 0.8rem; }
.note-field {
  flex: 1 1 200px;
  min-width: 160px;
  padding: 5px 8px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-size: 0.85rem;
}
.page-foot { margin-top: 28px; display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.batch-id { color: var(--muted); font-size: 0.8rem; margin: 0; }
"""

_SCRIPT = """
(function () {
  "use strict";
  function pad(value) { return value < 10 ? "0" + value : String(value); }
  function formatLocalTimestamp(date) {
    return (
      date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate()) +
      "T" + pad(date.getHours()) + ":" + pad(date.getMinutes()) + " (local)"
    );
  }
  function storageKey(hash) { return "zhiphoto." + ZHIPHOTO_BATCH_ID + "." + hash; }
  function readOverride(hash) {
    try {
      var raw = window.localStorage.getItem(storageKey(hash));
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") return null;
      return parsed;
    } catch (err) {
      return null;
    }
  }
  function writeOverride(hash, state) {
    try {
      window.localStorage.setItem(storageKey(hash), JSON.stringify(state));
    } catch (err) {
      /* localStorage unavailable (private mode, restricted context); the toggle still
         updates the DOM for this session, it just will not survive a reload. */
    }
  }
  function effectiveState(entry) {
    var override = readOverride(entry.hash);
    if (override) {
      return {
        tested: !!override.tested,
        tested_at: override.tested_at || null,
        note: typeof override.note === "string" ? override.note : ""
      };
    }
    return { tested: entry.tested, tested_at: entry.tested_at, note: entry.note || "" };
  }
  function updateProgress() {
    var testedCount = 0;
    ZHIPHOTO_ENTRIES.forEach(function (entry) {
      if (effectiveState(entry).tested) testedCount += 1;
    });
    var el = document.getElementById("progress-count");
    if (el) el.textContent = "tested " + testedCount + "/" + ZHIPHOTO_ENTRIES.length;
  }
  function renderEntry(entry) {
    var state = effectiveState(entry);
    var checkbox = document.getElementById("tested-" + entry.index);
    var timestampEl = document.getElementById("timestamp-" + entry.index);
    var noteEl = document.getElementById("note-" + entry.index);
    if (checkbox) checkbox.checked = state.tested;
    if (timestampEl) {
      timestampEl.textContent = state.tested_at ? "tested at " + state.tested_at : "not tested yet";
    }
    if (noteEl && document.activeElement !== noteEl) noteEl.value = state.note;
  }
  function persist(entry, tested, note) {
    var state = {
      tested: tested,
      tested_at: tested ? formatLocalTimestamp(new Date()) : null,
      note: note || ""
    };
    writeOverride(entry.hash, state);
    renderEntry(entry);
    updateProgress();
  }
  function copyText(text, button) {
    var original = button.textContent;
    function onDone() {
      button.textContent = "Copied";
      window.setTimeout(function () { button.textContent = original; }, 1500);
    }
    function fallback() {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.top = "-1000px";
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand("copy");
      } catch (err) {
        /* nothing more we can do in this context */
      }
      document.body.removeChild(textarea);
    }
    if (window.navigator.clipboard && window.navigator.clipboard.writeText) {
      window.navigator.clipboard.writeText(text).then(onDone, function () {
        fallback();
        onDone();
      });
    } else {
      fallback();
      onDone();
    }
  }
  function exportState() {
    var entries = ZHIPHOTO_ENTRIES.map(function (entry) {
      var state = effectiveState(entry);
      return {
        prompt_hash: entry.hash,
        tested: state.tested,
        tested_at: state.tested_at,
        note: state.note
      };
    });
    var payload = {
      schema: "zhiphoto-prompt-batch-state/v1",
      batch_id: ZHIPHOTO_BATCH_ID,
      exported_at: formatLocalTimestamp(new Date()),
      entries: entries
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    var url = window.URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = ZHIPHOTO_BATCH_ID + "-state.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.setTimeout(function () { window.URL.revokeObjectURL(url); }, 1000);
  }
  function init() {
    ZHIPHOTO_ENTRIES.forEach(function (entry) {
      renderEntry(entry);
      var checkbox = document.getElementById("tested-" + entry.index);
      var noteEl = document.getElementById("note-" + entry.index);
      if (checkbox) {
        checkbox.addEventListener("change", function () {
          persist(entry, checkbox.checked, noteEl ? noteEl.value : "");
        });
      }
      if (noteEl) {
        noteEl.addEventListener("input", function () {
          var tested = checkbox ? checkbox.checked : effectiveState(entry).tested;
          persist(entry, tested, noteEl.value);
        });
      }
      var copyButton = document.getElementById("copy-" + entry.index);
      if (copyButton) {
        copyButton.addEventListener("click", function () {
          var pre = document.getElementById("prompt-" + entry.index);
          copyText(pre ? pre.textContent : "", copyButton);
        });
      }
    });
    updateProgress();
    var exportButton = document.getElementById("export-state");
    if (exportButton) exportButton.addEventListener("click", exportState);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
"""


def _json_for_script(data: Any) -> str:
    """Serialize `data` for embedding inside an inline <script> element.

    json.dumps output can legally contain the substring "</" inside a string value
    (e.g. an agent-written note), which would prematurely close the surrounding
    <script> tag when embedded raw. Escaping "</" to "<\\/" is a no-op for JSON/JS
    string parsing but inert as HTML, so arbitrary baked text can never break the page.
    """
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def _kind_label(kind: str) -> str:
    return "Modification" if kind == "modification" else "Generation"


def _badge_class(reference: ReferenceInfo) -> str:
    return "badge-required" if reference.expected else "badge-optional"


def _render_entry(entry: BatchEntry) -> str:
    index = entry.index
    checked_attr = " checked" if entry.tested else ""
    timestamp_text = (
        f"tested at {html.escape(entry.tested_at)}" if entry.tested_at else "not tested yet"
    )
    badge_text = (
        f"Reference required — {html.escape(entry.reference.instruction)}"
        if entry.reference.expected
        else "No reference needed"
    )
    return (
        f'<section class="entry" id="entry-{index}">\n'
        f'<header class="entry-head">\n'
        f'<h2><span class="ordinal">#{index}</span> '
        f'<span class="anchor">{html.escape(entry.anchor)}</span></h2>\n'
        f'<div class="chips">\n'
        f'<span class="chip chip-kind">{html.escape(_kind_label(entry.kind))}</span>\n'
        f'<span class="chip chip-type">{html.escape(entry.type)}</span>\n'
        f'<span class="chip chip-profile">{html.escape(entry.profile)}</span>\n'
        f'</div>\n'
        f'</header>\n'
        f'<div class="badge {_badge_class(entry.reference)}">{badge_text}</div>\n'
        f'<div class="prompt-block">\n'
        f'<div class="prompt-toolbar">\n'
        f'<span class="hash" title="prompt hash">hash {html.escape(entry.prompt_hash)}</span>\n'
        f'<button type="button" class="copy-button" id="copy-{index}">Copy prompt</button>\n'
        f'</div>\n'
        f'<pre class="prompt-text" id="prompt-{index}">{html.escape(entry.prompt)}</pre>\n'
        f'</div>\n'
        f'<div class="tested-row">\n'
        f'<label class="tested-toggle">'
        f'<input type="checkbox" id="tested-{index}"{checked_attr}> Tested</label>\n'
        f'<span class="timestamp" id="timestamp-{index}">{timestamp_text}</span>\n'
        f'<input type="text" class="note-field" id="note-{index}" maxlength="280" '
        f'placeholder="optional note" value="{html.escape(entry.note)}">\n'
        f'</div>\n'
        f'</section>\n'
    )


def render_html(batch: Batch) -> str:
    entries_html = "".join(_render_entry(entry) for entry in batch.entries)
    total = len(batch.entries)
    # Progress count: baked from batch.json here (so the page is meaningful even with
    # JS disabled, and so identical input always renders identical bytes), then
    # overwritten client-side on load by _SCRIPT's updateProgress() -- localStorage can
    # hold overrides the baked batch.json does not know about, so JS is the source of
    # truth for what's on screen; this function only picks the initial paint.
    tested_count = sum(1 for entry in batch.entries if entry.tested)
    manifest = [
        {
            "index": entry.index,
            "hash": entry.prompt_hash,
            "tested": entry.tested,
            "tested_at": entry.tested_at,
            "note": entry.note,
        }
        for entry in batch.entries
    ]
    plural = "" if total == 1 else "s"
    parts = [
        "<!doctype html>\n",
        '<html lang="en">\n<head>\n',
        '<meta charset="utf-8">\n',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
        f"<title>{html.escape(batch.batch_id)} — ZhiPhoto Prompts</title>\n",
        f"<style>{_STYLE}</style>\n",
        "</head>\n<body>\n",
        '<main class="page">\n',
        '<header class="page-head">\n',
        "<h1>ZhiPhoto Prompt Batch</h1>\n",
        f'<p class="brief"><strong>Brief:</strong> {html.escape(batch.brief)}</p>\n',
        (
            '<p class="meta">'
            f'<span id="entry-count">{total} prompt{plural}</span>'
            f' &middot; <span id="progress-count">tested {tested_count}/{total}</span>'
            "</p>\n"
        ),
        (
            '<p class="reminder">Copy each prompt into your own ChatGPT session and attach '
            "references yourself where a badge asks for one. This page never opens, links "
            "to, or submits anything to chatgpt.com.</p>\n"
        ),
        "</header>\n",
        '<section class="entries">\n',
        entries_html,
        "</section>\n",
        '<footer class="page-foot">\n',
        '<button type="button" id="export-state">Export tested state</button>\n',
        (
            f'<p class="batch-id">Batch id: {html.escape(batch.batch_id)} &middot; created '
            f"{html.escape(batch.created_at)}</p>\n"
        ),
        "</footer>\n",
        "</main>\n",
        "<script>\n",
        f"var ZHIPHOTO_BATCH_ID = {_json_for_script(batch.batch_id)};\n",
        f"var ZHIPHOTO_ENTRIES = {_json_for_script(manifest)};\n",
        _SCRIPT,
        "</script>\n",
        "</body>\n</html>\n",
    ]
    return "".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _local_timestamp() -> str:
    """Local timestamp for `tested_at`, matching the schema's own `created_at`
    convention (design doc example: "2026-08-31T14:20 (local)")."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M") + " (local)"


def _default_render_path(batch_path: Path) -> Path:
    # Design choice: batch.json carries no field recording where a page was last
    # rendered (the schema in the design doc is fixed and doesn't have one), and
    # decision 10 already establishes that regeneration for a batch happens in place
    # "same folder, same batch_id". So `mark`/`ingest` always retarget the default
    # location alongside batch.json rather than tracking history out-of-band; an
    # explicit `--out` on `render` is a one-off override, not a sticky setting.
    return batch_path.parent / "prompts.html"


def _find_entry(batch: Batch, *, index: int | None, prompt_hash: str | None) -> BatchEntry:
    if index is not None:
        for entry in batch.entries:
            if entry.index == index:
                return entry
        raise PromptPageError(f"no entry with index {index} in batch {batch.batch_id!r}")
    for entry in batch.entries:
        if entry.prompt_hash == prompt_hash:
            return entry
    raise PromptPageError(f"no entry with prompt_hash {prompt_hash!r} in batch {batch.batch_id!r}")


def cmd_render(args: argparse.Namespace) -> int:
    batch_path = Path(args.batch).resolve()
    batch = load_batch(batch_path)
    out_path = Path(args.out).resolve() if args.out else _default_render_path(batch_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(batch), encoding="utf-8")
    print(f"rendered {len(batch.entries)} entries to {out_path}")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    if args.tested is None and args.note is None:
        raise PromptPageError("mark requires --tested and/or --note")
    batch_path = Path(args.batch).resolve()
    batch = load_batch(batch_path)
    entry = _find_entry(batch, index=args.index, prompt_hash=args.prompt_hash)
    if args.tested is not None:
        tested = args.tested == "true"
        entry.tested = tested
        entry.tested_at = _local_timestamp() if tested else None
    if args.note is not None:
        entry.note = args.note
    save_batch(batch, batch_path)
    out_path = _default_render_path(batch_path)
    out_path.write_text(render_html(batch), encoding="utf-8")
    print(f"marked entry {entry.index} (hash {entry.prompt_hash}) tested={entry.tested}; re-rendered {out_path}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    batch_path = Path(args.batch).resolve()
    state_path = Path(args.state).resolve()
    batch = load_batch(batch_path)
    state = load_state(state_path)
    entries_by_hash = {entry.prompt_hash: entry for entry in batch.entries}
    updated = 0
    skipped = 0
    for state_entry in state["entries"]:
        entry = entries_by_hash.get(state_entry["prompt_hash"])
        if entry is None:
            # Matching is by prompt_hash, never by index (decision 7): an unmatched
            # hash means the prompt changed or the entry was removed since export, and
            # there is nothing meaningful to update -- skip silently, as specified.
            skipped += 1
            continue
        entry.tested = state_entry["tested"]
        entry.tested_at = state_entry["tested_at"] if entry.tested else None
        entry.note = state_entry["note"]
        updated += 1
    save_batch(batch, batch_path)
    out_path = _default_render_path(batch_path)
    out_path.write_text(render_html(batch), encoding="utf-8")
    entry_word = "entry" if updated == 1 else "entries"
    hash_word = "hash" if skipped == 1 else "hashes"
    print(
        f"ingested {state_path}: updated {updated} {entry_word}, skipped {skipped} unmatched "
        f"{hash_word}; re-rendered {out_path}"
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="render prompts.html from a batch.json manifest")
    render.add_argument("--batch", required=True, help="path to batch.json")
    render.add_argument("--out", help="output HTML path (default: prompts.html beside batch.json)")

    mark = commands.add_parser("mark", help="set tested/tested_at/note on one entry and re-render")
    mark.add_argument("--batch", required=True, help="path to batch.json")
    identify = mark.add_mutually_exclusive_group(required=True)
    identify.add_argument("--index", type=int, help="1-based entry index to mark")
    identify.add_argument("--hash", dest="prompt_hash", help="entry prompt_hash to mark")
    mark.add_argument("--tested", choices=("true", "false"), default=None)
    mark.add_argument("--note", default=None, help="optional short note to store on the entry")

    ingest = commands.add_parser(
        "ingest", help="merge an exported tested-state file by prompt_hash and re-render"
    )
    ingest.add_argument("--batch", required=True, help="path to batch.json")
    ingest.add_argument("--state", required=True, help="path to an exported batch-state.json")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "render":
            return cmd_render(args)
        if args.command == "mark":
            return cmd_mark(args)
        if args.command == "ingest":
            return cmd_ingest(args)
    except PromptPageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
