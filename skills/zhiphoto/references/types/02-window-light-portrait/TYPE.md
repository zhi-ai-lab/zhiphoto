---
schema: image-type/v2
type_version: 1
id: 02-window-light-portrait
title: Natural Window-Light Portrait
summary: Close camera portraits photographed by a real camera with soft window light, truthful skin texture, and restrained analog film character.
keywords: ["window-light portrait", "window portrait", "natural light close-up", "50mm portrait", "35mm film portrait", "unretouched portrait", "窗边人像", "窗边近距离人像", "自然光人像", "真实皮肤", "胶片颗粒"]
category: portrait
profile_kind: look
fallback: false
required_refs: ["references/types/02-window-light-portrait/foundations/window-portrait-realism.md"]
reference_policy: optional
reference_role: likeness
sort_order: 40
---

# Natural Window-Light Portrait Type

Compose a close camera portrait lit by a real window, preserving the user's subject, identity, framing, mood, styling, palette, and output requirements. Apply the selected look profile only as a delta over the required foundation.

This type reads as an intimate photograph made by a separate camera rather than a selfie, beauty campaign, or synthetic render. Do not infer a default age, gender, ethnicity, nationality, or appearance when the user leaves those attributes open; preserve the subject they specify or let the generator choose a varied, plausible person.

When the request implies a phone held by the subject, prefer the selfie type. When it asks for illustration, heavy retouching, or an intentionally artificial look, prefer another type.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
