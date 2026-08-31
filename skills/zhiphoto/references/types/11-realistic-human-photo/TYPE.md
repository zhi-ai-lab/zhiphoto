---
schema: image-type/v2
type_version: 1
id: 11-realistic-human-photo
title: Realistic Human Photo
summary: Unretouched, documentary-grade photorealistic photographs of people taken with a real camera, prioritizing true skin texture over selfie geometry or stylization.
keywords: ["realistic portrait", "hyperreal portrait", "photorealistic person", "documentary portrait", "skin texture", "no retouching", "no beauty filter", "超写实人像", "写实人像", "真实皮肤质感"]
category: portrait
profile_kind: look
fallback: false
required_refs: ["references/types/11-realistic-human-photo/foundations/human-photo-realism.md"]
reference_policy: optional
reference_role: likeness
sort_order: 30
---

# Realistic Human Photo Type

Compose a camera-photographed, documentary-realistic image of a person while preserving the user's subject, framing, lighting, palette, and output choices. Apply the selected look profile only as a delta over the required foundation.

This type reads as a photograph taken of the subject by a separate camera. When the request instead implies a phone held by the subject, prefer the selfie type. When the request asks for stylization, illustration, or heavy retouching, this type does not apply.

Subjects must be unmistakably adults; use age 25+ when an adult age is unspecified. Do not sexualize the subject beyond what the user explicitly requests.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
