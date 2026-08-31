---
schema: image-profile/v1
profile_version: 1
id: character-sheet
type: 10-personal-ip
kind: identity
title: Reusable Personal IP Character Sheet
summary: A clean single-image square specification sheet that locks a human-derived IP across identity, views, expressions, actions, palette, and reuse guidance.
keywords: ["character bible", "turnaround", "expression sheet", "action sheet", "personal IP system", "人物设定表", "角色三视图"]
maturity: general
adult_only: false
sort_order: 20
---

# Reusable Personal IP Character Sheet

## Use When

Use this profile when the user wants to establish the canonical version of a person-derived character for repeated future scenes. Before composing the prompt, read [format-sheet.md](../format-sheet.md) and inspect [personal-ip-demo.png](../personal-ip-demo.png) with a vision-capable tool when available. Treat the result as one visual specification sheet, not as several unrelated illustrations.

Exactly one unambiguous, user-supplied reference image — attached to the request, or loaded via `view_image` from a customer-provided path — must be established before the `image_gen` call. Use that image for appearance only. Use the current character-information brief for role semantics. Never inherit a character from earlier turns in this session; if the user says to ignore previous character information, state that reset in the prompt and follow it.

## Profile Deltas

- Generate one clean square specification sheet on a white or very light neutral background, following the information architecture in `format-sheet.md` and the visual hierarchy of `personal-ip-demo.png` without copying its example character.
- Include these seven readable modules: IP name and standard image information; a prominent Canonical Avatar; labeled turnaround/multi-view references; labeled expressions; labeled role-specific action poses; an independent Color Theme area with swatches, names, and exact HEX values; and concise usage guidance.
- The demo's counts are illustrative rather than rigid. Let the model choose the number of views, expressions, actions, anchors, and colors that fit legibly in one square image, but do not omit a required module.
- Keep the same face geometry, hair, glasses or facial hair, signature accessory, adult proportions, outfit, footwear, and colors in every panel. Change only pose, expression, orientation, and role-specific props.
- Derive the outfit and props from the current character-information brief. For the specific pose, gesture, and orientation in each panel, instruct the image model to decide from the reference image itself — including any text, caption, or label visible in it — together with the character-information brief's role; do not pre-write a fixed list of action poses into the composed prompt yourself. Never treat clothing or objects visible in a source poster as permanent identity without explicit instruction.
- Use generous spacing, rounded panel separators, simple rows, flat colors, rounded outlines, minimal shading, and short Chinese labels. Make every figure readable at small size and easy to reproduce consistently.
- Keep text compact: short headings, short labels, short usage bullets, and exact HEX values. Do not ask the image model to render long biographies or dense paragraphs.

## Profile-Specific Avoidances

- Do not redesign the character between turnaround views, expressions, or action poses.
- Do not add generic office or creator props when the stated profession has more authentic tools.
- Do not include poster copy, contact details, interface chrome, decorative backgrounds, watermarks, a second unrelated character, or a cinematic scene collage.
