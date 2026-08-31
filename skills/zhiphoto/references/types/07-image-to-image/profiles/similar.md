---
schema: image-profile/v1
profile_version: 1
id: similar
type: 07-image-to-image
kind: usage
title: Similar
summary: Takes the reference's family traits — genre, mood, palette family, composition family, subject category — and generates a clearly distinct new instance.
keywords: ["one like this", "similar image", "same vibe", "同款图片", "同款再画", "类似的图"]
maturity: general
adult_only: false
sort_order: 40
---

# Similar

## Use When

Use when the customer wants another one of these — same kind of image — without pinning a style change or a new subject; also the default fit when the brief names no usage at all ("参考这张图出一张").

## Profile Deltas

- Take from the reference: genre, mood, palette family, composition family, subject category.
- Invent fresh: a distinct new instance — new specific subject and arrangement within that family.
- Default aspect: the reference's own aspect ratio, unless the customer states one.

## Profile-Specific Avoidances

- Never a near-duplicate of the reference — vary the specific subject and arrangement enough that the output is unmistakably a new image.
- Do not drift genre — stay within the reference's family traits.
- Never carry over text, watermarks, or logos from the reference.
