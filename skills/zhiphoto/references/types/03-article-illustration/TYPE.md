---
schema: image-type/v2
type_version: 1
id: 03-article-illustration
title: Article Illustration
summary: Standalone 16:9 article illustrations that turn cognitive anchors into sparse, hand-drawn visual metaphors, preferring a customer-provided recurring character template and falling back to Xiaohei only when no template was supplied.
keywords: ["article illustration", "正文配图", "文章插图", "怪诞手绘", "personal ip template", "xiaohei", "方法论配图"]
category: illustration
profile_kind: scene
fallback: false
required_refs: ["references/types/03-article-illustration/foundations/style-dna.md", "references/types/03-article-illustration/foundations/xiaohei-ip.md", "references/types/03-article-illustration/foundations/composition-patterns.md", "references/types/03-article-illustration/foundations/prompt-template.md", "references/types/03-article-illustration/foundations/qa-checklist.md", "references/types/03-article-illustration/foundations/personal-ip-reference.md"]
reference_policy: required
reference_role: recurring-template
consumes: identity-template
sort_order: 22
---

# Article Illustration

Read every required foundation before composing the final prompt. The foundations adapt `ian-xiaohei-illustrations` into ZhiPhoto's type/profile contract while keeping the sparse hand-drawn article-illustration language and preferring a customer-supplied recurring personal IP when available.

Prefer a customer-explicit personal-IP template when the customer indicates one should be used. Obtain the template image — already attached this run, or ask the customer to attach it or point to a local file — and load it into context with `view_image` if it is a local file not already visible in context. Use that image as the recurring identity reference for every shot in this run. If no template intent was supplied at all, use the original Xiaohei fallback described in `xiaohei-ip.md`. If the customer did indicate template intent but no usable template image can be obtained, stop and report the blocker instead of falling back. The reference image controls identity only; it is not a request to copy the template sheet's layout or text into the article illustration.

Use `single-article-illustration` by default, including when the source material is a full article or long post but the customer asked for only one illustration. Use `article-illustration-series` only when the customer explicitly asks for multiple images, provides an explicit shot list, or requests a set/series. If the customer wants multiple illustrations but does not give a count, ask for the count before generation.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
