# Prompt-Handoff Transport

This is the shared contract for lane P: composing a batch of one or more prompts and
presenting them as a local, self-contained web page for a human to run themselves, by
hand, in their own chatgpt.com session. It defines the input contract, composing each
entry, the reference-indicator derivation, the `batch.json` manifest contract, invoking
`scripts/prompt_page.py`, the no-automation guardrails, and the completion report. This
transport never calls `image_gen` and never opens, links to, scripts, or submits
anything to chatgpt.com or any website — the only deliverable is prompts. Do not replace
it with a browser, an API script, Computer Use, or any website interaction.

This is the sibling to `references/transport/codex-image-gen.md`. That transport calls
`image_gen` directly and exports an image; this one never does. Read `codex-image-gen.md`
for the automatic path and its pre-generation confirmation gate — that gate's one added
response path converts a live generation run into this transport mid-flight (see
**Arriving here from the confirmation gate** below).

This transport supports one output mode: **batch mode.** An ordered list of N ≥ 1
entries — each one a fully composed prompt for a single shot, produced by the exact
upstream routing, type/profile selection, and prompt-composition steps in `SKILL.md` — is
rendered as one manifest (`batch.json`) and one page (`prompts.html`) per run. There is no
per-entry gate and no per-entry web call: every entry is composed in full before the page
is rendered once, at the end of the run.

## Inputs

Determine these before composing any entry:

- `count`: the number of entries, N. Reuses the exact count rules already in `SKILL.md`'s
  **Select output mode**: an explicit customer-given N ("generate 10 prompts…") fixes the
  count exactly; a request that is clearly plural but gives no count ("give me some
  prompts for…") asks the customer for the count before composing any entry; a singular
  request ("give me a prompt for…") produces exactly one entry. Even N = 1 goes through
  this same batch shape — this transport has no separate single-entry mode (design
  decision 4).
- `entries`: the ordered shot list. For N > 1, build it the same way series mode builds a
  shot list today — one cognitive anchor per shot, recurring identity/visual language
  held stable across entries per `SKILL.md`'s **Compose the final prompt** — before
  composing any individual entry's final prompt.
- `batch_stem`: `prompts-<short-slug>`, a short filesystem-safe slug derived from the
  request's subject (for example `prompts-window-portraits`). The `prompts-` prefix is
  fixed — it keeps batch runs visually distinct from image runs in a directory listing.
- `output_directory`: resolved the same way as the image transport's output directory.
  When the customer names a directory explicitly, use it exactly as given — no run
  subfolder is imposed. Otherwise default to
  `.local/output/<batch_stem>-<YYYYMMDDTHHmm>/` under the current workspace, using the
  Mac's current local time at run start. Create it if absent. Regeneration for the same
  batch happens in place — same folder, same `batch_id` — which is what keeps the page's
  localStorage namespace stable across re-renders.
- `batch_id`: the resolved per-run folder's basename (for example
  `prompts-window-portraits-20260831T1420`) — the same string whether the folder came
  from the default path or an explicit override that happens to follow that shape; an
  explicit customer-named folder that doesn't follow that shape simply becomes `batch_id`
  as given.
- `brief`: the customer's request, verbatim, recorded in `batch.json`'s header.

For a run converted mid-flight from the confirmation gate, `output_directory` was already
reserved by the sidecar the gate wrote in its step 1 — reuse that folder rather than
reserving a second one; see **Arriving here from the confirmation gate**.

## Compose each entry

Every entry is composed exactly as an ordinary generation or modification would be,
through the end of prompt composition, and then diverted here instead of continuing to
`codex-image-gen.md`:

1. Route and select type/profile per `SKILL.md`'s **Resolve prompt guidance dynamically**
   and **Choose from route candidates** — identical to the image path. All entries in one
   batch share one type/profile unless the request itself describes a mixed batch (rare;
   `batch.json`'s per-entry `type`/`profile` fields exist for this, see **The batch.json
   contract**).
2. Resolve reference handling per `SKILL.md`'s **Resolve reference handling** — read
   `reference_policy` and `reference_role` from the selected type's `resolve` output. This
   step is upstream, unchanged reuse; it only tells the agent whether a reference is
   normally in play for this type, not whether this transport attaches one anywhere (it
   never does — see **Reference-indicator derivation**).
3. Compose the final prompt per `SKILL.md`'s **Compose the final prompt**, or the delta
   prompt per **Modify an existing image** for a `kind: modification` entry. Composing a
   prompt may still call `view_image` on a locally available reference file to write a
   more accurate prompt — a first-party tool call, not a website visit — and this is
   unrelated to whether the human will need to attach that file in their own ChatGPT
   session; see the next section.
4. Compute `prompt_hash` = the first 8 hex characters of `sha256(prompt)` over the exact
   final prompt text, UTF-8 encoded.
5. Fill this entry's `reference` object (below) and append the entry to `entries[]`.

Repeat for every entry before writing `batch.json`. Do not call `prompt_page.py render`
until every entry is filled — batch mode renders the page once, at the end, not
incrementally per entry.

## Reference-indicator derivation

For every entry, fill `reference` from two things: the selected type's own
`reference_policy`/`reference_role` (from `resolve`'s output — the same fields the
automatic path already reads via `SKILL.md`'s **Resolve reference handling**), and this
specific entry's actual composed prompt. The two can disagree, and `expected` follows the
entry, not the type default:

- `policy`: copied from the type's `reference_policy` (`required` or `optional`). For a
  `kind: modification` entry, always `required` — the delta prompt only makes sense
  relative to a known edit target (`SKILL.md`'s **Modify an existing image**).
- `role`: copied from the type's `reference_role`. For a `kind: modification` entry,
  always `edit-target`.
- `expected`: `true` only when this entry's actual composed prompt assumes an attachment
  will be present in the ChatGPT message that submits it — not merely whether the type
  generally supports one. Two cases commonly diverge from a naive
  "`policy == required` → `expected: true`" reading:
  - A `required`-policy type whose own guidance defines a no-reference fallback that this
    entry actually used (for example `article-illustration` falling back to its built-in
    Xiaohei style when no template was supplied) → `expected: false`; the composed prompt
    is self-contained.
  - A `required`-policy type whose reference is consumed only during *composition*, never
    re-attached in the final prompt (for example `image-to-post-cover`: the agent viewed
    the source image to extract and condense its words, but its fixed generation prompt
    never re-attaches or references the source image — see that type's own `TYPE.md`) →
    `expected: false`.
  - Conversely, an `optional`-policy type (`window-light-portrait`, `selfie`, `general`,
    `candid-car-flash-photo`, `realistic-human-photo`) is `expected: true` only for the
    entries that actually used a supplied likeness reference; other entries in the same
    batch legitimately carry `expected: false` — this is the "may differ entry-to-entry
    even within one batch" case.
  - A `required`-policy type with no fallback (`personal-ip`, `image-to-image`,
    `ip-based-post-cover`) is `expected: true` for every entry, since there is no route to
    a composed prompt without one.
- `instruction`: one sentence, written fresh for this entry, telling the human what to
  attach in their ChatGPT session and why — derived from the selected type's own
  reference guidance (its `TYPE.md` and required foundations), never a static per-type
  string copy-pasted across entries. Leave it `""` when `expected` is `false`.
  Representative shapes — write the actual sentence per entry, do not reuse these
  verbatim:
  - `personal-ip`: "Attach the same reference photo you used to establish this
    character's identity, so the sheet keeps their visible identity."
  - `ip-based-post-cover` / `article-illustration` when a template is in use: "Attach
    your character reference sheet to the same message, so the cover keeps the
    character's established identity."
  - `image-to-image`: "Attach the visual source you provided to the same message — this
    shot restyles it per the `restyle` profile." (name the actual selected profile and
    what it takes from the reference.)
  - An optional-likeness type, for an entry that used a supplied likeness reference:
    "Attach the reference photo you shared, so this portrait's likeness matches it."
  - A `kind: modification` entry: "Attach the exact image you want modified to the same
    message — the prompt above describes only the change to make to it."

## The batch.json contract

`batch.json` is the authoritative record; `prompts.html` is a render of it. Schema
`zhiphoto-prompt-batch/v1`:

```json
{
  "schema": "zhiphoto-prompt-batch/v1",
  "batch_id": "prompts-window-portraits-20260831T1420",
  "created_at": "2026-08-31T14:20 (local)",
  "brief": "<customer request verbatim>",
  "entries": [
    {
      "index": 1,
      "anchor": "short shot topic",
      "kind": "generation",
      "type": "window-light-portrait",
      "profile": "natural-close-up",
      "prompt": "<full final prompt, byte-for-byte>",
      "prompt_hash": "<first 8 hex of sha256(prompt)>",
      "reference": {
        "policy": "optional",
        "role": "likeness",
        "expected": false,
        "instruction": ""
      },
      "tested": false,
      "tested_at": null,
      "note": ""
    }
  ]
}
```

- `index` is 1-based and matches the entry's position in the ordered shot list.
- `anchor` is the entry's short cognitive-anchor label, the same concept series mode
  already uses.
- `kind` is `generation` or `modification`. A `modification` entry's `prompt` is the delta
  prompt ("change only X, keep everything else identical" — `SKILL.md`'s **Modify an
  existing image**), and its `reference.role` is `edit-target`.
- `type`/`profile` are omitted (or left empty) for a `modification` entry, since there is
  no type/profile selection for a modification. They live per entry, not at the batch
  level, so a future mixed batch needs no schema change — but a v1 run composes one brief
  → one type/profile per batch, one `kind` mix (generation batch, or a single
  modification entry) at most.
- `prompt_hash` is the first 8 hex characters of `sha256(prompt)`, UTF-8 encoded. It keys
  the tested-state mechanism (see `prompt_page.py mark`/`ingest` below): a regenerated
  batch keeps the `tested` mark for any entry whose prompt text is unchanged, and resets
  it for any entry whose prompt text changed — a "tested" mark attests to exact prompt
  text, not to an ordinal position.
- `tested`/`tested_at`/`note` start `false`/`null`/`""` on first render. They are the
  disk-truth mirror of the page's localStorage toggle state; `prompt_page.py mark` and
  `prompt_page.py ingest` are what update them from disk (see below).
- There are no per-prompt `.prompt.md` sidecars in batch mode — the sidecar convention
  pairs a prompt with a generated *image*, and batch mode produces no image. `batch.json`
  carries every prompt verbatim instead.

## Invoke prompt_page.py

Once `batch.json` is fully composed — every entry filled, per **Compose each entry** —
render the page:

```bash
python3 skills/zhiphoto/scripts/prompt_page.py render --batch <path-to-batch.json>
```

This writes `prompts.html` beside `batch.json` in the same `output_directory`,
deterministically from the manifest (same `batch.json` bytes in, same `prompts.html`
bytes out). Never hand-author or hand-edit `prompts.html` directly — it is always a
render of the manifest, never independently maintained content.

Two further subcommands update `batch.json`'s tested state after the initial render, then
re-render `prompts.html` so the page reflects the update:

- `mark` — sets one or more entries' `tested` state (and optional `note`) by index or by
  `prompt_hash`. Use this when the customer tells the agent directly which entries passed
  ("mark 2, 5, 9 tested") instead of exporting from the page.
- `ingest` — merges an exported `batch-state.json` (downloaded from the page's "Export
  tested state" button) back into `batch.json`, matched by `prompt_hash`.

This file documents `render`'s invocation exactly, since it is the one call every run
makes. `mark` and `ingest` are invoked later, only when reconciling tested state (see
**Completion report**); their precise flag spelling is `prompt_page.py`'s own contract —
run `python3 skills/zhiphoto/scripts/prompt_page.py mark --help` or `... ingest --help`
if unsure, rather than guessing. Both rewrite `batch.json` in place and re-render
`prompts.html` from the updated manifest, keeping the page and the manifest in sync.

## No-automation guardrails

- Never open, navigate to, link to, script, or submit anything to chatgpt.com or any
  website from this transport or from the rendered page. The page's only mention of
  ChatGPT is a plain-text reminder that the human pastes the prompt into their own
  session — never a hyperlink, never an auto-navigation, never a form submission target.
- Never call `image_gen` from this transport, for any entry. If the customer wants an
  image actually generated, that request belongs to lane A or lane G in
  `codex-image-gen.md` — do not silently substitute a generated image for a requested
  prompt page, and do not silently substitute a prompt page for a requested image.
- The human performs all generation, all reference-attachment, and all image review
  themselves, in their own ChatGPT session. This transport's responsibility ends at
  rendering `prompts.html` and reporting; it never fetches, verifies, or scores anything
  the human does afterward in ChatGPT.
- Never submit, upload, or transmit a prompt or a reference file to any remote service
  from this transport — every operation here is a local file read or write.
- If `prompt_page.py` is unavailable or its `render` call fails, stop and report the exact
  blocker. Do not fall back to hand-authoring an HTML page (the renderer is a
  deterministic script by design, not per-run authored HTML) and do not fall back to any
  browser-based or API-based path.
- Do not skip the reference-indicator derivation for any entry, even when `policy` is
  `optional` and no reference was used for that entry — that entry still needs an
  explicit `reference` object recording `expected: false`, so absence is a stated fact,
  not an omission.
- Do not call `image_gen`, ever, as part of composing or rendering a batch — composing a
  prompt is reasoning and local file I/O only.

## Page constraints

`prompts.html` is a single self-contained, offline HTML file: inline CSS/JS only, zero
network requests, works from `file://`. No external fonts or CDNs, no images, and no
hyperlink to chatgpt.com anywhere in the page. Copy buttons, the Tested toggle, and the
export/import mechanics are the page's own concern. This transport file governs
`batch.json`'s content and the `render`/`mark`/`ingest` invocations that produce and
update the page; the page's actual HTML/CSS/JS implementation is `scripts/prompt_page.py`'s
contract, not reproduced here.

## Arriving here from the confirmation gate

`codex-image-gen.md`'s pre-generation confirmation gate has one added response path (see
its **The pre-generation confirmation gate** section): if the customer answers the gate's
ask with something equivalent to "just give me the prompt(s), I'll run them in ChatGPT
myself," the run converts to this transport instead of calling `image_gen`.

- The prompt(s) already composed and saved as `.prompt.md` sidecar(s) by the gate's step 1
  become this batch's entries — reuse that composed text and that reserved
  `output_directory` rather than recomposing the prompt or reserving a second location.
- For a series run converted mid-flight (some shots already generated as images before
  this exit was taken), compose the remaining shots' prompts to complete the shot list —
  this transport has no per-shot gate, so there is nothing further to ask before
  composing them — and render one page covering the whole batch, not just the shots
  composed after the conversion.
- Everything else in **Inputs**, **Compose each entry**, and **Reference-indicator
  derivation** above applies unchanged; the only difference from a batch requested as
  prompts from the start is where the first entry's prompt text came from.

## Completion report

Return:

- The absolute `output_directory` path.
- The entry count.
- A one-line reference summary per entry: ordinal, anchor, and reference expectation —
  for example `1. window-light close-up — no reference needed` or `4. personal IP mark —
  reference required: attach the identity photo`.
- How the customer can mark entries tested:
  - **In the page:** open `prompts.html` locally and use each entry's Tested toggle —
    this writes to the browser's `localStorage` immediately and survives reopening the
    same file. The page's "Export tested state" button downloads `batch-state.json`,
    which is then ingested back into `batch.json` with
    `python3 skills/zhiphoto/scripts/prompt_page.py ingest --batch <path-to-batch.json> --state <path-to-batch-state.json>`.
  - **Directly through the agent:** the customer tells the agent which entries passed
    ("mark 2, 5, 9 tested"), and the agent runs `prompt_page.py mark` against the
    corresponding indices, then re-renders the page.
- Confirmation that no `image_gen` call was made and no website was opened during this
  run.
