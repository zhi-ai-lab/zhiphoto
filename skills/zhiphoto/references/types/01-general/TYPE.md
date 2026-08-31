---
schema: image-type/v2
type_version: 1
id: 01-general
title: General Image
summary: Direct fallback for any image request that does not meaningfully match a specialized image type.
keywords: ["general image", "illustration", "photo", "artwork", "graphic", "fallback"]
category: general
profile_kind: mode
fallback: true
required_refs: ["references/types/01-general/foundations/direct-prompt.md"]
reference_policy: optional
reference_role: likeness
sort_order: 1000
---

# General Image Type

Use this fallback when no specialized type materially improves the user's request. Preserve the brief directly and avoid adding a specialized aesthetic, subject model, or composition system that the user did not request.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
