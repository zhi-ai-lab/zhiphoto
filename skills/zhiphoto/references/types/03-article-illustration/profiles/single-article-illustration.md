---
schema: image-profile/v1
profile_version: 1
id: single-article-illustration
type: 03-article-illustration
kind: scene
title: Single Article Illustration
summary: One standalone 16:9 illustration for a single article, post, method, workflow, state, or conceptual metaphor, using the customer's recurring personal-IP template when supplied and Xiaohei otherwise.
keywords: ["single article illustration", "正文插图", "article illustration", "knowledge content illustration", "概念隐喻"]
maturity: general
adult_only: false
sort_order: 10
---

# Single Article Illustration

## Use When

Use for one generated image that explains a single cognitive anchor from prose in any language or a short conceptual brief. This remains the default even when the source material is a full article or long post, unless the customer explicitly asks for multiple images, a shot list, or a series. If the user asks for several images, use `article-illustration-series` instead.

## Profile Deltas

- Select one judgment, transition, input/output relationship, state change, or metaphor; do not summarize the whole article in one image.
- Generate one standalone 16:9 horizontal image with a pure white background, generous empty space, sparse short annotations in the user's requested language when needed, and an original low-tech visual metaphor.
- If the customer indicates that a personal-IP template should be used, obtain the template image — already attached this run, or ask the customer to attach it or point to a local file — and load it into context with `view_image` if it is a local file not already visible in context. Use it as the recurring reference for this illustration. Keep its stable identity, illustration language/style, and signature palette consistent while placing the character inside the illustration's core action.
- If no customer-explicit template was supplied at all, use the Xiaohei fallback described in `xiaohei-ip.md`.
- If the customer did indicate template intent but no usable template image can be obtained, stop and report the blocker instead of falling back.
- Keep the recurring character, whether customer-specific or Xiaohei fallback, as an active participant in the central action, not as a decorative side character.

## Profile-Specific Avoidances

- Do not reproduce the personal-IP character sheet's grid, labels, palette swatches, or biography as the article illustration.
- Do not turn the image into a PPT slide, formal flowchart, dense explainer, poster, mascot sheet, or title card.
- Do not reuse the package's example compositions; invent a fresh metaphor for the current brief.
- Do not add long copy. Keep annotations short, use the user's requested language, and omit them when they are not necessary.
