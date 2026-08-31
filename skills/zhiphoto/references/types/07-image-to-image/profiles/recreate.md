---
schema: image-profile/v1
profile_version: 1
id: recreate
type: 07-image-to-image
kind: usage
title: Recreate
summary: Keeps the reference subject's appearance and invents a new scene, situation, or context around it.
keywords: ["same subject new scene", "put this in a new scene", "同一主体换场景", "把它画到", "换个场景重画"]
maturity: general
adult_only: false
sort_order: 20
---

# Recreate

## Use When

Use when the customer wants to keep the thing or person from the reference, but in a new scene, situation, or context — 把这只猫画到太空里, "same product, on a beach".

## Profile Deltas

- Take from the reference: the subject's appearance — identity features, colors, distinctive details.
- Invent fresh: scene, background, lighting, composition, weather, per the brief.
- Default aspect: the reference's own aspect ratio, unless the customer states one.

## Profile-Specific Avoidances

- Do not import the reference's background or props into the new scene — it is explicitly left behind.
- Do not alter the subject's identity — appearance, colors, and distinctive details carry over faithfully.
- When the subject is an identifiable real person, `foundations/real-person-boundary.md` binds hardest here — read it before composing.
- Never carry over text, watermarks, or logos from the reference.
