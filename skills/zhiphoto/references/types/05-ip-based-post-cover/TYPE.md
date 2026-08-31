---
schema: image-type/v2
type_version: 1
id: 05-ip-based-post-cover
title: IP-Based Post Cover
summary: 3:4 vertical feed covers for text posts and video-post thumbnails that turn "this episode in one sentence" into bold cover copy acted out by the customer's recurring IP character from a required reference sheet.
keywords: ["ip post cover", "post cover", "video thumbnail", "cover image", "人设封面", "小红书封面", "封面图", "视频封面", "帖子封面", "一句话封面"]
category: illustration
profile_kind: layout
fallback: false
required_refs: ["references/types/05-ip-based-post-cover/foundations/cover-language.md"]
reference_policy: required
reference_role: recurring-template
consumes: identity-template
sort_order: 23
---

# IP-Based Post Cover

Read `foundations/cover-language.md` before composing the final prompt. It defines the shared cover language — inputs, character fidelity, the fixed palette, the three copy lines, and the feed-composition rules — that every profile in this type applies as a delta.

This type produces one cover per request: the cover image of a text post or the thumbnail of a video post. Both use the same 3:4 vertical cover language; the post kind does not change the profile choice.

The character reference sheet is mandatory. There is no built-in fallback character for this type: if no sheet is available, stop and ask the customer to supply one — never invent a character or borrow one from another type. The agent obtains the sheet per `SKILL.md`'s **Resolve reference handling** — already attached this run, or ask the customer to attach one or point to a local file — then loads it into context with `view_image` and passes it to `image_gen` labeled `reference`, per the transport reference's **Reference and edit-target handling**. The sheet controls identity only — face, hair, glasses, beard, clothes, body, line, and style. It is not a request to reproduce the sheet's grid, labels, palette swatches, or biography on the cover.

Two layout profiles interpret the same one-sentence input differently:

- `big-type-cover` — type carries the cover; the sentence is compressed to the shortest line that still lands at a glance. Default by catalog order.
- `title-illustration-cover` — a complete-sentence title plus one clear illustration of the character acting it, with deliberate whitespace.

Select by which reading fits the sentence and the customer's ask; when both fit equally, catalog order applies.

Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification).
