---
schema: image-type/v2
type_version: 1
id: 06-image-to-post-cover
title: Image-to-Post Cover
summary: Reads the large main-section words out of a customer-supplied image directly — the agent views the image itself, then extracts and condenses the words in its own reasoning — and renders a freshly invented 3:4 xiaohongshu realistic-photography cover carrying at most two lines of Chinese — the source image contributes words only, never visuals.
keywords: ["image to post cover", "screenshot to cover", "cover from image text", "photo quote cover", "screenshot words cover", "words in screenshot", "turn screenshot into cover", "xiaohongshu cover", "从截图出封面", "图里的字做封面", "文字截图封面", "小红书摄影封面", "写实摄影封面", "把图片文字做成封面", "截图里的文字", "截图里的字", "截图里的话", "提取截图文字", "截图文字"]
category: general
profile_kind: layout
fallback: false
required_refs: ["references/types/06-image-to-post-cover/foundations/text-extraction.md", "references/types/06-image-to-post-cover/foundations/condense-prompt.md", "references/types/06-image-to-post-cover/foundations/cover-prompt.md"]
reference_policy: required
reference_role: text-source
sort_order: 21
---

# Image-to-Post Cover

Read all three required foundations, in this order, before composing anything: `foundations/text-extraction.md` (what counts as main-section text, and how the agent reads it from the viewed image), `foundations/condense-prompt.md` (the fixed rules the agent applies to condense the extracted text into four fields), and `foundations/cover-prompt.md` (the fixed generation prompt submitted to `image_gen` — the only step that actually generates an image).

This type is a strict vertical — exactly the *words* mode of a broader image-to-cover family. The attached image contributes words only, never visuals: its palette, layout, composition, scene, and subjects must never influence the generated cover. Only the four condensed field values — never a description or restatement of the image itself — enter the final generation prompt, and that prompt never re-attaches or references the source image, even though the agent viewed it during extraction. A request for a cover that looks like the attached image ("照这张图的感觉出一张") does not belong to this type's words-only pipeline; route it to `image-to-image` instead — a cover-shaped ask there lands as `similar` or `style-transfer`, with the customer's format words (小红书, 3:4, 封面, etc.) carried into that type's composed prompt as ordinary brief content. Never approximate a look-alike request with this type's words pipeline.

## Reference handling and the extraction/condensation/generation sequence

The agent obtains the screenshot per `SKILL.md`'s **Resolve reference handling** — already attached this run, or ask the customer to attach one or point to a local file — exactly like `ip-based-post-cover`. `template_intent` for this type's run is `true`.

Once one intended source image is identified (resolve ambiguity first, see below), the agent runs three steps of its own reasoning, in this same session, before calling `image_gen`:

1. **Extraction** (`foundations/text-extraction.md`) — `view_image` the source image, then read the main-section words directly out of it, applying that foundation's criteria for what counts as main-section text (or recognizing that none is readable).
2. **Condensation** (`foundations/condense-prompt.md`) — condense the extracted words (or the customer's pasted words, in the no-readable-text recovery path) into exactly four lines — 主句/收束/画面/光线 — applying that foundation's rules, then check the result against those rules itself before proceeding.
3. **Generation** (`foundations/cover-prompt.md`) — compose the fixed verbatim template with the four condensed field values filled in, and call `image_gen`. This is the only step that actually generates an image, and the only step the transport's pre-generation confirmation gate and generation-time verification/retry rules apply to — extraction and condensation are the agent's own reasoning, not generation attempts.

If multiple candidate images are attached or visible and the intended screenshot is ambiguous, follow `SKILL.md`'s ambiguity rule (stop and ask which one) before extraction.

Handle these cases:

- **No image supplied**: the reference is mandatory (`reference_policy: required`, no fallback) — stop and ask the customer to supply one before generation can proceed. Never invent text, never proceed from the request prose alone, never borrow another type's fallback.
- **The agent's own extraction finds no readable main-section text**: report exactly what the agent found (or didn't find) in the image, then offer two recovery options in one question: attach a different image (restart from extraction with a fresh `view_image`), or paste the intended main-section words as text directly in the agent conversation. A pasted-text recovery skips extraction and resumes at condensation, with 原文： filled from the customer's pasted text instead of the agent's own extracted words — the image-first contract is otherwise unchanged.
- **The agent's own extraction is ambiguous about which text is the main section** (it finds several candidate blocks with no clear primary one): report the candidates verbatim and ask the customer to pick before composing the condensation step.
- **The agent's own condensation does not come back as exactly four lines matching the shape rules**: redo the condensation once (at most one retry) rather than inventing or editing field values. If it still fails, stop and report the malformed result.
- **Customer wants the image's look, not its words**: this is not this type's request — route to `image-to-image` (typically `similar` or `style-transfer`) instead of running the words pipeline as an approximation.

## Profile

One profile, `xiaohongshu-photo-cover`, covers this type today — both fixed prompts already hard-code the platform, aspect, and text hierarchy, leaving no variation axis for a second profile to own.

## Provenance and the prompt sidecar

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification). This type's sidecar additionally records, in the Provenance section, the agent's own extraction (the main-section words verbatim) and the four condensed lines from the agent's own condensation (主句/收束/画面/光线) — the exact record that makes an extraction or condensation miss auditable after the fact.
