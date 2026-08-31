---
schema: image-type/v2
type_version: 1
id: 10-personal-ip
title: Personal IP Character
summary: Reference-led human character design that distills a person into a simple, reusable visual identity or character sheet.
keywords: ["personal IP", "IP character", "cartoon avatar", "character sheet", "IP logo", "真人IP", "卡通形象"]
category: portrait
profile_kind: identity
fallback: false
required_refs: ["references/types/10-personal-ip/foundations/identity-extraction.md"]
reference_policy: required
reference_role: identity-source
produces: identity-template
sort_order: 26
---

# Personal IP Character

Read the identity-extraction foundation first, then apply exactly one identity profile as a delta. The current supplied reference image establishes visible identity; the current character-information brief establishes the role and semantic world.

This type is for a new, reusable visual character derived from a supplied reference image. It is not for a realistic portrait, a one-off caricature, or an open-ended mascot unrelated to the supplied person.

## User input and output contract

The supported request has this shape:

1. The user supplies the intended reference photo to Codex, either as an attachment to the request or by pointing to a local file path.
2. Codex loads that reference image with `view_image` to confirm it is visible and unambiguous before composing the prompt.
3. The user invokes ZhiPhoto with character information and an exact destination, for example:

   `use [$zhiphoto](/path/to/zhiphoto/SKILL.md) to generate personal IP set with character information as <character information>, save the output to <file location>`

The successful output is one personal-IP set image saved to the exact file location requested by the user. Use the `character-sheet` profile for a set; use `canonical-mark` only when the user explicitly asks for one compact avatar or character mark.

If no reference image has been supplied or attached this run, or multiple candidate images are ambiguous, stop and ask the customer which one to use, or to supply one, before proceeding. Do not silently substitute an older reference, an unrelated local file, or a text-only character description.

## Format reference

The `character-sheet` profile has a maintained format reference at [format-sheet.md](format-sheet.md) and the sibling visual exemplar [personal-ip-demo.png](personal-ip-demo.png). A vision-capable agent should inspect the exemplar before writing the generation prompt. It defines the sheet's information architecture and visual hierarchy, not the identity of the example character. Keep the seven modules, square composition, and reusable reference-sheet function while allowing creative choices inside them.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
