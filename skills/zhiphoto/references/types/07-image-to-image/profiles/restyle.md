---
schema: image-profile/v1
profile_version: 1
id: restyle
type: 07-image-to-image
kind: usage
title: Restyle
summary: Keeps the reference's subject, pose, composition, and scene layout, and re-renders everything in a customer-named target style, medium, or look.
keywords: ["restyle", "art style change", "换个画风", "转绘", "风格化重绘"]
maturity: general
adult_only: false
sort_order: 10
---

# Restyle

## Use When

Use when the customer names a target style, medium, or look for the attached image's own content — "make this Ghibli style", 把这张照片变成水彩. This includes a whole-image style request phrased as an edit ("把这张图改成油画风") once the customer has confirmed reference intent per `TYPE.md`'s "Choosing between modification and this type".

## Profile Deltas

- Take from the reference: subject count, poses, composition, and scene layout.
- Invent fresh: rendering style, medium, texture, and palette, per the style the customer named.
- Default aspect: the reference's own aspect ratio, unless the customer states one.

## Profile-Specific Avoidances

- Do not add or remove subjects or objects from the reference's composition.
- Do not recompose the scene — keep the layout the reference established.
- Do not keep photographic realism when a non-photo style is named.
- Never carry over text, watermarks, or logos from the reference.
