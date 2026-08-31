---
schema: image-profile/v1
profile_version: 1
id: article-illustration-series
type: 03-article-illustration
kind: scene
title: Article Illustration Series
summary: An ordered set of standalone 16:9 illustrations that maps cognitive anchors to separate images while keeping either the customer's recurring personal IP or the Xiaohei fallback stable across the full set.
keywords: ["article illustration series", "multiple article illustrations", "multilingual shot list", "多张正文配图", "文章配图策略", "多图配图"]
maturity: general
adult_only: false
sort_order: 20
---

# Article Illustration Series

## Use When

Use only when the customer explicitly asks for multiple images, an image count greater than one, a shot list, or a set/series of illustrations. A full article or long post by itself does not trigger this profile.

## Profile Deltas

- First extract an ordered shot list of distinct cognitive anchors.
- If the user explicitly requests `N` images, the shot list must contain exactly `N` shots.
- If the user requests multiple images but does not specify a count, ask for the count before generation.
- Each shot gets one core action, structure, state, or metaphor and its own standalone 16:9 image. Generate each shot separately and save separate files in shot-list order.
- Keep the recurring identity stable across every shot. When the customer indicates template intent, obtain and load the template image once at the start of the series — already attached this run, or ask the customer to attach it or point to a local file, loading it into context with `view_image` if needed — then reuse that same image unchanged for every shot in the series, unless the customer supplies a different one mid-series. Preserve its identity, illustration language/style, and signature palette.
- If no customer-explicit template was supplied at all, use the Xiaohei fallback consistently across the full series.
- If the customer did indicate template intent but no usable template image can be obtained, stop and report the blocker instead of falling back.
- Give the user the short shot list before generation when the request asks for planning. Otherwise proceed once the image count is explicit.

## Profile-Specific Avoidances

- Do not ask the image model for a collage, contact sheet, comic grid, or one canvas containing all shots.
- Do not summarize the whole article in every image or reuse one metaphor for every shot.
- Do not silently stop after the first shot. Track the ordered list and verify/export every generated file before delivery.
- Do not add long copy, a series title, or shot numbers to the artwork unless the user requests them.
