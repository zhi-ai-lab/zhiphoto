---
schema: image-profile/v1
profile_version: 1
id: xiaohongshu-photo-cover
type: 06-image-to-post-cover
kind: layout
title: Xiaohongshu Photo Cover
summary: The standard 3:4 realistic-photography cover — 主句 largest, 收束 second, collapsing to one line when 收束 is 无, rendered by the fixed verbatim generation prompt.
keywords: ["xiaohongshu photo cover", "3:4 photo cover", "two-line photo cover", "小红书3:4摄影封面", "两行大字摄影封面", "截图文字摄影", "screenshot cover"]
maturity: general
adult_only: false
sort_order: 10
---

# Xiaohongshu Photo Cover

## Use When

Use when the customer wants the *words* in an attached image turned into a cover — a screenshot or photo whose main-section text should drive a freshly generated 小红书 3:4 realistic-photography cover. This does **not** apply when the customer wants a cover that looks like the attached image (its palette, layout, composition, scene, or subjects) — that request routes to `image-to-image` instead, never approximated by this profile.

## Profile Deltas

- Apply `foundations/text-extraction.md`, `foundations/condense-prompt.md`, and `foundations/cover-prompt.md` in order — extraction, condensation, generation — exactly as written; this profile adds no variation on top of the fixed prompts — the platform (小红书), aspect (3:4), text hierarchy, and style (写实摄影) are already hard-coded in `cover-prompt.md`.
- Follow the 收束=无 flow-through in `foundations/cover-prompt.md`: always fill the 收束 line, with 无 when there is no closing line, and let the generation prompt's own rule collapse it to a single line.
- After export, verify per `foundations/cover-prompt.md`'s Verification section: exactly one line of Chinese when 收束 is 无, exactly two otherwise, 主句 visibly largest, and the rendered characters matching the condensed fields.

## Profile-Specific Avoidances

- Do not let the source image's palette, layout, composition, scene, or subjects influence the generated cover in any way, even though the agent viewed the image during extraction — the image contributes words only, and the cover is invented fresh each time (每次换一套和原意有关的现场). Generation never restates or references the image.
- Do not add any text to the image beyond the two allowed lines (主句/收束) — no restated aspect ratio, no method tag, no English.
- Do not render a frontal face close-up; people, when present, are back-view, distant, or in silhouette only.
