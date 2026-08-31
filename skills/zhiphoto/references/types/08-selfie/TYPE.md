---
schema: image-type/v2
type_version: 1
id: 08-selfie
title: Selfie
summary: Realistic phone-held self-portraits with scene-aware capture geometry, lighting, expression, and human detail.
keywords: ["selfie", "phone portrait", "social photo", "arm's length", "mirror selfie"]
category: portrait
profile_kind: scene
fallback: false
required_refs: ["references/types/08-selfie/foundations/selfie-realism.md", "references/types/08-selfie/foundations/prompt-assembly.md"]
reference_policy: optional
reference_role: likeness
sort_order: 20
---

# Selfie Type

Compose a scene-aware selfie prompt while preserving the user's subject, setting, mood, styling, lighting, and framing choices. Apply the selected scene profile only as a delta over the required foundations.

Read `modifiers/identity-continuity.md` only when the request supplies a reference person or requires a repeatable identity. Subjects in sexualized or sensual profiles must be unmistakably adults; use age 25+ when an adult age is unspecified. Follow the selected profile's boundaries without needlessly diluting a permitted adult request.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
