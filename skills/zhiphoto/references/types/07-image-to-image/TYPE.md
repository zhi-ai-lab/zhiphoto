---
schema: image-type/v2
type_version: 1
id: 07-image-to-image
title: Image-to-Image
summary: Generates a new image informed by a customer-attached visual source — restyle it, recreate its subject in a new scene, transfer its style to a new subject, or make another one like it — with the reference reaching `image_gen` as a labeled input the agent loads and passes itself, and each profile fixing what is taken from the reference versus invented fresh.
keywords: ["image to image", "make one like this", "in the style of this image", "style transfer", "restyle this photo", "recreate from this image", "generate from reference image", "visual reference generation", "以图生图", "照这张图再画", "照这张图的感觉", "风格迁移", "参考这张图生成", "按这张图的风格", "用这张图当参考", "换个风格重画"]
category: general
profile_kind: usage
fallback: false
required_refs: ["references/types/07-image-to-image/foundations/visual-source-usage.md", "references/types/07-image-to-image/foundations/real-person-boundary.md"]
reference_policy: required
reference_role: visual-source
sort_order: 25
---

# Image-to-Image

Read both required foundations before composing anything: `foundations/visual-source-usage.md` (the take/invent/exclude prompt-composition discipline, new-image phrasing, and the aspect-ratio default) and `foundations/real-person-boundary.md` (what a real-person visual source permits and refuses — read this before composing any prompt that carries an identifiable person's likeness into the output).

This type covers the general "here is an image — make me a new one informed by it" family: restyle it, recreate its subject in a new scene, transfer its style to a new subject, or make another one like it. It is deliberately not a cover format — `image-to-post-cover` (words-only) and `ip-based-post-cover` (recurring-character covers) stay their own types. A cover-shaped ask that names visual resemblance to an attached image (for example "照这张图的感觉出一张封面") lands here instead, typically as `similar` or `style-transfer`, with the customer's format words (小红书, 3:4, 封面, etc.) carried into the composed prompt as ordinary brief content — not as a fixed cover template.

## Reference handling

The visual source reaches `image_gen` as a labeled input: the agent obtains the file per `SKILL.md`'s **Resolve reference handling** (already attached this run, or ask the customer to attach one or point to a local file), loads it into context with `view_image` if it is a local file not already visible in context, then passes it to `image_gen` labeled by role — see the transport reference's **Reference and edit-target handling**. `template_intent` for this type's run is `true`. `reference_policy: required`, no fallback: without the image there is no brief to work from — stop and ask the customer to attach one; never invent a visual source from prose alone, never borrow another type's fallback.

## Choosing between modification and this type

`SKILL.md`'s existing fork ("Modification" vs "Generation", and its follow-up "If it is unclear whether an attached image should be edited as-is or used only as a reference for a new image, ask the customer") already disambiguates before routing reaches this type — no second question exists here. One refinement lives in this type's own guidance rather than in `SKILL.md`: a whole-image style conversion ("把这张图改成油画风") is structurally a `restyle`, because the modification contract — "change only X, keep everything else identical" — is unkeepable when X is the entire rendering. If the customer answers the existing fork question with "edit it in place" for such a request, proceed with the modification flow as asked, but state its drift caveat plainly and mention this type's `restyle` profile as the alternative in the same message; the customer decides. One honest sentence, not a new gate.

## Selecting a profile

Four `usage` profiles fix what is taken from the reference versus invented — `restyle`, `recreate`, `style-transfer`, `similar` (catalog order). Select by which profile's Use When matches what the brief names:

- Names a target style/medium/look for the reference's own content → `restyle`.
- Keeps the reference's subject but wants a new scene/situation → `recreate`.
- Wants the reference's *look* applied to a *different* subject named in the brief → `style-transfer`.
- Wants "another one like this" with no style change and no new subject pinned, or names no usage at all → `similar`.

When the brief plausibly fits two or three of these, ask one plain question offering the plausible readings — the router's existing several-plausible rule, no new mechanism. When it genuinely fits none more than another, catalog order resolves it: `restyle` first.

## Provenance and the prompt sidecar

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification). This type's sidecar additionally records, in the Provenance section, the selected profile and the take/invent/do-not-carry-over statement as composed — the record of what the reference was used for.
