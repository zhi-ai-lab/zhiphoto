---
name: zhiphoto
description: Generate new images and modify existing ones — an image zhiphoto just produced, or one the customer attaches — through Codex's built-in image generation ability by routing any image request to extensible type and profile guidance, then verifying each artifact. Use for any image an agent is asked to generate or change, or for a request whose deliverable is prompts instead of images (e.g. "generate 10 prompts", "give me prompts to test in ChatGPT myself") — the same routing composes and hands off a batch of prompts as a local page rather than generating images. Default to single-image output unless the selected profile explicitly defines a series; do not use for general batch generation.
---

# ZhiPhoto

Keep the user's exact subject, setting, mood, styling, lighting, composition, aspect ratio, language, and output requirements authoritative.

After each terminal customer run, make one best-effort attempt to write a minimized typed ZhiCoach report using `scripts/zhicoach_report.py` and `references/zhicoach-reporting.md`; reporting must never hide or delay the user outcome, and eval, zhicoach, and report-writing runs must be suppressed.

## Determine generation vs modification

Before anything else, decide which workflow this request needs:

- **Modification**: the request asks to change, fix, adjust, add, or remove something in an image already produced earlier in this run, or in an image the customer attaches specifically to be altered — not supplied as an identity/style/likeness reference for a new image. Follow **Modify an existing image** below instead of the routing funnel.
- **Generation**: everything else — a request to produce a new image, whether or not a reference is involved. Continue with **Resolve prompt guidance dynamically**.

If it is unclear whether an attached image should be edited as-is or used only as a reference for a new image, ask the customer before proceeding.

## Resolve prompt guidance dynamically

Run these commands from this skill directory:

1. Note whether the customer has supplied, or clearly intends to supply, a reference image for this request.
2. Run `python3 scripts/image_catalog.py route --brief "<the request, in its own words>" --has-reference yes|no --format json`.
3. Apply **Choose from route candidates** below to settle on exactly one type. Do not settle on a type from its raw score alone.
4. Run `python3 scripts/image_catalog.py resolve --type <type-id> --format json`. Read the returned `type_path` file and every file in `required_ref_paths`.
5. Run `python3 scripts/image_catalog.py list-profiles --type <type-id> --format json`.
6. Select the profile whose metadata best matches the request. If multiple profiles are equally suitable, use the catalog order, which is deterministic by `sort_order` and then ID.
7. Run `python3 scripts/image_catalog.py resolve --type <type-id> --profile <profile-id> --format json`, then read the returned `profile_path` file.

Do not hard-code or enumerate type or profile identifiers in this router. Catalog discovery is authoritative, so future valid types and profiles require no `SKILL.md` change.

## Choose from route candidates

`route` returns a short, scored shortlist — never load the whole catalog by default, and never treat the raw top score as automatically final.

- **One clear winner:** exactly one type stands out — either a decisive score lead over every other type in the shortlist, or the rest of the shortlist is just that same type's other profiles — and its `matched_terms` plausibly relate to the request's actual subject. Proceed with that type without asking.
- **Several plausible:** two or three distinct types are each a reasonable fit (close scores, or each matches a different real aspect of the request). Present those 2-3 candidates to the customer with one-line reasons each, drawn from their `category` and what matched, and let them pick.
- **Weak or unreliable shortlist:** the leading score is driven only by a single generic or incidental term (a common word with no real bearing on the request's subject), or competing types are tied with no meaningful signal either way. Before concluding there is no match, run `python3 scripts/image_catalog.py list-types --format json` (or `--grouped`) and read every type's `title`/`summary` directly against the request — keyword scoring can miss a genuine match when the request phrases a type's concept in different words than its keywords. If that direct read surfaces a clear or plausible fit, treat it as such under the two rules above.
- **No meaningful match:** nothing in the shortlist or the full type list fits. Fall back to the type marked `fallback: true` and mention the nearest misses (the highest-scoring types that still did not fit) in the response.

## Resolve reference handling

For a fresh generation, the selected type's `resolve` output carries `reference_policy` (`required` or `optional`) and `reference_role` (what a supplied reference means here — for example an identity source, a recurring template, or a likeness aid). Use those fields, not prose about the request's intent, to decide whether a reference is needed:

- `reference_policy: required` and no reference is available yet: a reference is mandatory — ask the customer to supply one (attach it, or point to a local file) before generation can proceed for this type.
- `reference_policy: optional` and the customer supplied or intends to supply a reference: obtain the file, then use it per this type's `reference_role`.
- `reference_policy: optional` and no reference was supplied: proceed without one.
- A type's own guidance may define a no-reference fallback for its `reference_role` (for example, the built-in Xiaohei illustration used when no template is supplied). When that fallback applies, use the fallback instead of asking for a reference.

For a **modification** of a customer-supplied image (see **Modify an existing image** below), obtaining the image is always mandatory — there is no type/profile lookup for a modification, so this is simply how the image to modify is identified.

When a reference or edit-target image is needed: obtain the file — it may already be attached this run, or ask the customer to attach it or point to a local file when it is not. If multiple current-request attachments or described candidates could plausibly be the intended one, ask the customer which one to use. Once identified, the file flows into `references/transport/codex-image-gen.md`'s **Reference and edit-target handling** section, which owns loading it into context (via `view_image` when needed) and passing it to `image_gen` labeled by role. There is no website step and no "paste it into this chat" instruction — the agent handles the file directly as a Codex tool input.

## Select output mode

- Default to single-image output.
- Follow the selected profile when it explicitly defines a series workflow or another output shape.
- If the user explicitly asks for `N` images, produce exactly `N` shots.
- If the user clearly wants multiple images but does not specify a count, ask for the count before generation.
- In series mode, first create a concise ordered shot list. Each shot must have one cognitive anchor and its own prompt. Generate and save each shot as a separate image; never compress the set into a collage or stop after the first shot.

## Modify an existing image

Two supported cases:

- **(a) Iterating on an image zhiphoto generated earlier in this run.** Use `image_gen`'s edit mode on the image already visible in this session's context and submit a delta prompt. No fresh type/profile routing and no new reference lookup are needed — the image, already visible from having been generated earlier this session, carries over unchanged as the edit target.
- **(b) Modifying an image the customer supplies.** The customer's image is obtained via **Resolve reference handling** above, then the delta prompt is submitted as an `image_gen` edit call using that image as the edit target. There is no type/profile selection for this case.

In both cases, phrase every delta prompt as "change only X, keep everything else identical" — name exactly what should change and state explicitly that everything else must stay the same. Do not restate the entire original description; naming untouched details invites the model to redraw them differently.

State this contract plainly to the customer: image generation regenerates the whole image rather than patching pixels, so unrequested drift in untouched areas can occur even from a precise delta prompt. After every modification, compare the before and after images, report any changes the customer did not ask for, and let the customer decide whether to accept the result or retry.

Follow **Select output mode** and **Generate, export, and verify** as usual to generate, place, and verify the modified image.

## Compose the final prompt

This section governs a fresh generation; a modification's prompt is composed per **Modify an existing image** instead.

Apply the selected profile as a delta over its type and required references. Preserve explicit user choices over defaults. Add only details that make the intended image or shot coherent and generatable; do not let profile defaults replace the request. For a series, keep any required recurring identity and visual language stable across shots while varying the shot-specific action, composition, and metaphor.

For adult profiles, require unmistakably adult subjects and follow the profile's adult boundaries and applicable platform safety requirements. Do not increase sexual intensity beyond the user's request.

## Select generation mode

Before prompt composition proceeds to a specific transport, decide which of three lanes this request belongs to. This is a property of the customer's own phrasing, not of the composed prompt text, so decide it as soon as the request is understood — no later than here, once type/profile targeting is settled for a fresh generation (or the edit target is identified for a modification). This step applies to every request, generation and modification alike. Evaluate in this order; the first match wins, so every request shape maps to exactly one lane:

- **(P) Prompt handoff** — the request's deliverable is *prompts*, not images: the customer explicitly asks for prompts rather than images ("generate 10 prompts", "give me prompts to run/test in ChatGPT myself", "make a prompt page", "出10个提示词", or equivalent explicit-prompt-deliverable phrasing). Continue to **Compose, present, and record** below. No `image_gen` call is made and no confirmation gate applies — nothing is spent, so there is nothing to gate.
- **(A) Auto-generate** — the deliverable is image(s) and the request explicitly says to generate directly ("generate the image directly", "just generate it", or equivalent). Continue to **Generate, export, and verify** below; unchanged behavior.
- **(G) Ask-then-generate** — the deliverable is image(s) with no generate-directly phrasing: the default when neither of the above matches. Continue to **Generate, export, and verify** below; unchanged behavior, including that transport's own pre-generation confirmation gate and its existing conversion path back into lane P (see `references/transport/codex-image-gen.md`) — nothing here alters or restates it.

**Disambiguation:** when a request plausibly reads both ways ("give me 10 covers to try in ChatGPT" — ten images, or ten prompts to run manually?), ask one plain clarifying question: "images generated here, or prompts for you to run yourself?" Absent any prompt-deliverable signal, default to images — generating images is the skill's core contract, and lane P fires only on explicit prompt phrasing, never inferred.

**Count rules:** lane P reuses the exact count logic already in **Select output mode** above — an explicit "N prompts" fixes the count exactly, a clearly-plural request with no count asks for the count before composing any entry, and a singular request produces exactly one entry. Lane P always emits `batch.json` + `prompts.html` covering the full entry set, N ≥ 1 included — one consistent artifact shape even for a single prompt. A modification request whose deliverable is prompts (the customer asks for the delta prompt to run themselves rather than an edited image) produces a one-entry page with `entries[0].kind: "modification"`.

## Compose, present, and record

Read and follow `references/transport/prompt-handoff.md` for lane P, once every entry's final prompt (or delta prompt) is composed. That transport reference exclusively owns the `batch.json` manifest contract, the reference-indicator derivation, invoking `scripts/prompt_page.py`, the no-automation guardrails, and the completion report. It never calls `image_gen` and never opens, links to, scripts, or submits anything to chatgpt.com or any other website — the only deliverable is prompts, for the customer to run themselves in their own ChatGPT session.

## Generate, export, and verify

Read and follow `references/transport/codex-image-gen.md` only after the final prompt or ordered shot prompts are ready. That transport reference exclusively owns reference/edit-target handling, the pre-generation confirmation gate, invoking the built-in `image_gen` tool, locating and placing its output, file naming, prompt-sidecar saving, and artifact verification. In particular, do not call `image_gen` before that transport file's pre-generation confirmation gate has run for the current prompt — it decides, per the customer's own phrasing, whether to proceed straight through or to save the prompt and ask permission first.

## Extend the catalog

Follow `references/image-profile-authoring.md`, then run:

```bash
python3 scripts/image_catalog.py validate
```
