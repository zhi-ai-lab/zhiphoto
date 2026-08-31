# ZhiPhoto Eval Suite — Runbook

Host note: generation uses Codex's built-in `image_gen` transport.

This is a complete unattended suite task: after the start prompt, finish every discovered
case without asking the human whether to continue, which case to run next, or whether to
retry. The human decides visual/content acceptance after the run; the agent only proves that
the requested transport returned and saved a usable artifact.

## Fixed reference bundle

All eval reference files are in `/Volumes/T7-APFS/Development/zhiphoto/.local/eval/`.
When a case names a reference, use that exact file rather than asking the human to attach or
choose another image: `03b-reference.png`, `05-reference.png`, `06-reference.png`,
`07-reference.png`, and `10-reference.png` match their case IDs. A missing named reference is
`SKIPPED (required reference missing)` and the suite continues; do not substitute an older
run artifact or invent a reference.

## Discovery

Do not hardcode case numbers or a case count. Glob `eval/cases/*.md` and process every
file found, in plain filename order. Filename order is what determines run order — the
`01b-modification.md` filename already sorts immediately after `01-general.md` and before
`02-window-light-portrait.md`, which is exactly the sequencing this case needs, so no reordering logic
is required.

That sequencing is load-bearing, not incidental: case 01b is a modification of case 01's
freshly generated image, and it has to use the image that remains visible in the same Codex
session. If case 01 fails or its export cannot be verified, mark case 01b's status
`SKIPPED (dependency: case 01 did not complete)` and do not attempt it standalone. Do not
load an unrelated image and try to fake the continuation.

Effective run order (illustrative — derive it fresh each run from whatever `eval/cases/`
currently contains): `01-general.md`, `01b-modification.md`, `02-window-light-portrait.md`, `03-illustration.md`,
`03b-illustration-with-reference.md`, `05-ip-based-post-cover.md`, `06-image-to-post-cover.md`,
`07-image-to-image.md`, `08-selfie.md`, `09-candid-car-flash-photo.md`, `10-personal-ip.md`,
`11-realistic-human-photo.md`.

## Pre-flight — before generating anything

Before starting case 01, do a routing-only dry pass over every discovered case. Generate
nothing during this pass.

For each case file (skip `01b-modification.md` here — it is a modification of case 01's
image, not a routed generation, so it has no catalog type to check):

1. Read the case's one-line brief. Note whether the brief itself indicates a reference is
   already available or clearly intended for that request (per `SKILL.md`'s "Resolve
   prompt guidance dynamically" step 1) — this decides the `--has-reference yes|no` value
   for routing, exactly as a real run would resolve it from the same brief.
2. From `/Users/jason/.agents/skills/zhiphoto/`, run
   `python3 scripts/image_catalog.py route --brief "<brief>" --has-reference yes|no --format json`.
   Apply `SKILL.md`'s **Choose from route candidates** decision procedure — clear winner /
   several plausible / weak-or-unreliable shortlist (check `list-types` directly before
   concluding no match) / no meaningful match (fallback type) — to settle on exactly one
   routed type, the same way a real run would. Do not just take the raw top score.
3. Run `python3 scripts/image_catalog.py resolve --type <type-id> --format json` and read
   `reference_policy`.
4. If `reference_policy` is `optional`, this case needs no pre-staged material.
5. If `reference_policy` is `required`, first check whether the case's own brief (per step
   1) already signals reference/template intent. If it does, this case needs pre-staged
   material regardless of whether the routed type also has a no-reference fallback — a
   fallback only rescues a case that supplies no reference at all, it does not excuse a
   case whose brief explicitly wants a real reference used. Only when the brief does NOT
   signal reference intent, check the routed type's own `TYPE.md` guidance for a
   no-reference fallback branch that a run would legitimately take when nothing is
   supplied (for example the built-in Xiaohei fallback for `03-article-illustration`). If such
   a fallback applies here, this case needs no pre-staged material either — note that it
   will use the fallback. If no such fallback exists for this type (or the brief signaled
   intent regardless of any fallback), this case needs the matching file from the fixed
   reference bundle before its generation attempt.

Collect every case flagged as needing material in step 5 into an internal list and resolve it
from the fixed reference bundle above. Do not present a pre-flight question to the human and
do not pause for attachment confirmation; the suite is required to finish unattended. If a
required file is absent, mark that case `SKIPPED (required reference missing)` immediately
and continue. For a present file, load it with `view_image` and use it as the named reference
without asking the human to identify it again.

## Execution parallelism and attempt policy

The suite may use up to three fresh subagent sessions in parallel, each using the Luna model
with `xhigh` effort. Each independent image-generation case must be assigned to a new
subagent/session; do not reuse one subagent for two independent generation cases. Case 01b is
the explicit exception: it must remain in the same session as case 01 because its edit target
is the image just generated there. The coordinator aggregates results after each case and owns the
single report file, so parallel workers must not overwrite one another's report sections.

Make exactly one generation attempt for each image case and exactly one edit attempt for case
01b. Never retry, regenerate, make an alternate shot, or keep an unscored variant after a
failure. A transport failure is recorded as `FAILED (generation error: <blocker>)` and the
suite continues; an extra generation is an execution defect and is not counted as a case
result.

## Reading and running each case

For each case file, in the effective run order above:

1. Extract the one-line "Brief to give zhiphoto" from the case file.
2. Run that brief through the normal zhiphoto workflow (`skills/zhiphoto/SKILL.md`)
   exactly as a real customer request — routing, reference handling, session mode,
   prompt composition, generation or prompt handoff, export, and verification, per that skill.
3. Check whether `eval/checklists/<same-basename>.md` exists (for example
   `eval/checklists/05-ip-based-post-cover.md` for `eval/cases/05-ip-based-post-cover.md`).
   - **If it exists:** read it for any operational notes at the top (such as case 01/01b's
     dependency) plus its `## Checklist` section. Verify the result against every mechanical
     item; visual/content items are marked `HUMAN_REVIEW_REQUIRED`, never judged by the agent.
   - **If it does not exist:** if the case file contains a `## Checklist` section, use that
     inline checklist; otherwise record whether the image generated successfully (or the
     prompt batch rendered successfully) and which type/profile it routed to. Note
     explicitly in the report when no formal checklist exists — do not invent criteria, and
     do not treat the absence of a checklist as a failure.
4. Skip any "Optional second shot" extension a case file or its checklist mentions — not
   part of a standard full-suite run.

## Continuing through failures

Never let one case's failure, skip, or missing checklist silently end the run. Move on to
the next case in the effective run order regardless of the previous case's outcome, except
for case 01b's hard dependency on case 01 above.

Do not pause mid-case for references, pre-generation confirmation, or session-mode questions;
the fixed reference bundle and unattended suite contract resolve those automatically. Never
pause to ask "should I continue?" — just continue.

## Output layout

At the very start of the run, once, create one top-level timestamped folder:
`.tmp/eval-<YYYYMMDDTHHmm>/` (local time, at run start).

Inside it, create one subfolder per case, named after that case's own file identifier —
for example `01-general/`, `07-image-to-image/`, `10-personal-ip/`. Case 01b gets its own
`01b-modification/` subfolder too (it has no catalog type of its own, but it still gets a
case-id subfolder). This per-case-id scheme is what keeps the layout unambiguous even for
a type-less case like 01b, and avoids collisions if two cases ever route to the same
catalog type.

Each case's subfolder holds its generated image and `<basename>.prompt.md` sidecar, per
the existing transport artifact contract
(`/Users/jason/.agents/skills/zhiphoto/references/transport/codex-image-gen.md`, **File
naming and artifact verification**). This run layout only changes the run's *base* output directory that
contract resolves into — the per-image naming and sidecar mechanics themselves stay
exactly as documented there.

The completed `.tmp/eval-<timestamp>/` folder is an audit record and is retained after the
suite finishes, including images, prompt sidecars, `batch.json`, `prompts.html`, and the
report. Do not automatically delete or clean this folder. Only disposable scratch outside
the run folder may be cleaned, and any later cleanup is a separate explicit operation.

## Report

Write `.tmp/eval-<YYYYMMDDTHHmm>/report.md`. Write it incrementally — update it after
every case completes or is skipped, not only once at the very end — so an interrupted run
still leaves an accurate record of everything actually finished.

Structure:

1. **Summary**, at the top: cases discovered, completed, generated successfully, failed,
   skipped (with skip reasons listed), and `Human review: pending` for visual/content
   acceptance.
2. **One section per case**, in the effective run order, each with:
   - Status: `COMPLETED` / `FAILED (<reason>)` / `SKIPPED (<reason>)`, where `COMPLETED`
     means only that the required local artifact or prompt batch was produced and passed
     mechanical checks.
   - Routed type/profile (or "modification of case 01" for case 01b).
   - Transport used (`codex-image-gen` or `prompt-handoff`) and `session_mode` when the
     workflow asked for one.
   - Mechanical checklist results when a checklist exists, or the "no checklist yet" note
     when it doesn't; visual/content rows must say `HUMAN_REVIEW_REQUIRED`.
   - Artifact paths (image and prompt sidecar).
   - Notes — for example the drift observation for case 01b, or the Xiaohei-fallback
     routing note for case 03, without turning visual judgments into agent scores.

Do not use OCR, image captioning, or visual semantic scoring to decide whether a case passed;
the agent's completion check is limited to route/transport bookkeeping, returned-file
integrity, prompt-sidecar or batch artifacts, and loadability/non-blank status.

## No resume mode

Every invocation of this runbook starts a fresh timestamped run folder from case 01 — do
not build a "resume a previous interrupted run" feature. The pre-flight skip-and-continue
behavior above is what keeps a normal run from stalling, so resume isn't needed for now.
