---
schema: image-profile/v1
profile_version: 1
id: style-transfer
type: 07-image-to-image
kind: usage
title: Style Transfer
summary: Takes the reference's palette, medium, texture, and compositional language, and applies it to a new subject named in the brief.
keywords: ["style transfer", "use this style", "用这个风格画", "风格套用", "照这个画风画"]
maturity: general
adult_only: false
sort_order: 30
---

# Style Transfer

## Use When

Use when the reference supplies the look and the brief supplies the subject — 用这张图的风格画一只龙, 风格迁移.

## Profile Deltas

- Take from the reference: palette, medium, line/texture quality, lighting mood, compositional language.
- Invent fresh: the subject and scene, entirely from the brief.
- Default aspect: the reference's own aspect ratio, unless the customer states one.

## Profile-Specific Avoidances

- Do not reproduce the reference's subject or any recognizable element of it — the style comes over, the content does not.
- Do not let the reference's actual scene or composition leak into the new subject's arrangement beyond the named style properties.
- Never carry over text, watermarks, or logos from the reference.
