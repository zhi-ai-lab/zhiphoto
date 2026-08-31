# Visual-Source Usage — Prompt Composition

No verbatim customer prompts exist for this type — unlike `image-to-post-cover`, every prompt is composed per run under this discipline.

1. **Always a new image, never an edit.** Every composed prompt requests *a new image using the attached image as reference* — the attached image is passed to `image_gen` as a labeled `reference` input, in **generate** mode, not **edit** mode. Edit-mode phrasing ("change this image…") would invoke `image_gen`'s edit semantics — which preserve/modify an existing image — and blur the modification boundary. If the request is actually a modification, it should never have reached this type; see `TYPE.md`'s "Choosing between modification and this type".
2. **The take/invent/exclude triple.** Every prompt names explicitly, per the selected profile:
   - what to **take** from the attached reference;
   - what to **invent** or change;
   - what must **not** carry over — each profile's complement (style-transfer: not the subject; restyle: not the medium; recreate: not the background; similar: not a near-copy) — plus, for every profile: no text, watermarks, or logos from the reference, and no text in the output unless the customer asks.

   Explicit complements are the guard against the image model's default of copying too much.
3. **Customer choices outrank profile defaults.** The standing `SKILL.md` composition rule applies unchanged — profile deltas fill gaps, they never override the brief.
4. **Aspect/format default.** When the customer names an aspect, it wins and is verified exactly against the exported file's dimensions, as usual. When they don't, the composed prompt requests *the same aspect ratio as the attached reference image* — the least surprising default for "one like this" — delegated to `image_gen` by explicit instruction, since the reference image is passed to it as a labeled input. Verification note: the agent now loads the reference image into context with `view_image` before generation (see the transport reference's **Reference and edit-target handling**), so with this default it verifies the output's aspect ratio directly against the reference image it already viewed, rather than only reporting a sensible-looking ratio without comparison; an explicitly stated aspect is verified against the exported file's dimensions as usual.
5. **Real-person guard hook.** When the reference clearly shows an identifiable real person and the selected profile carries that person into the output (`restyle`, `recreate`, `similar`), read and stay within `foundations/real-person-boundary.md` before composing the prompt — and never escalate intensity or context beyond the customer's words.

## Illustrative skeleton

Not a frozen template — each profile's Profile Deltas fill the middle three lines from its own take/invent/exclude contract.

```text
Generate one new image. Use the attached image as the visual reference.
Take from the reference: {profile take-list}.
Invent fresh: {profile invent-list, filled from the brief}.
Do not carry over: {profile complement}; no text, watermarks, or logos from the
reference; do not reproduce the reference itself.
Keep the same aspect ratio as the attached reference image.
```

When the customer names an explicit aspect ratio, replace the last line with that aspect ratio instead of the reference-matching instruction.
