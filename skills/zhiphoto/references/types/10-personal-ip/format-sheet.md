# Personal-IP Specification Sheet Format

This is the format contract for the `character-sheet` profile. Read it before composing a prompt, then inspect the sibling `personal-ip-demo.png` with a vision-capable tool when available. The demo is a layout and information-architecture reference only; do not copy its person, name, wardrobe, props, palette, or text.

## Required sheet structure

Return one complete square image containing these seven functional modules:

1. **IP name and standard image** — an IP name selected from the current brief, a clearly identified name/handle in the supplied reference, or by the image model, plus compact identity, temperament, stable marks, illustration style, and use cases. Keep the complete name inside its panel with comfortable margins.
2. **Canonical Avatar** — one prominent, independent portrait or avatar mark used as the primary recognition image.
3. **Turnaround / multi-view reference** — the same character in front, three-quarter, side, and back views, or an equally useful set of views, with short labels.
4. **Expression reference** — a row or group of reusable expressions with short labels.
5. **Action reference** — a row or group of reusable poses based on the supplied character information, with role-relevant gestures and props and short labels.
6. **Color Theme / 配色参考** — swatches with short color names and exact HEX values. The number and choice of colors are creative decisions, but this section must be present.
7. **Usage guidance** — short bullets explaining what must remain stable, what may change, and suitable applications.

The demo uses a rounded, lightly bordered grid: identity, avatar, and turnaround across the top; expressions and actions in the middle; color theme and usage guidance at the bottom. Preserve that clear hierarchy and readability, but allow the model to adapt the grid when the chosen character or language needs a different balance.

## Visual requirements

- Use one white or very light neutral square canvas, clear separators, generous spacing, and a clean flat/cartoon illustration language.
- Keep every panel legible at small size: thick or rounded contours, flat color masses, restrained shading, limited texture, and short Chinese labels. English may be used sparingly for `Canonical Avatar` and `Color Theme`.
- If the supplied reference is a poster or screenshot with a candidate IP name or handle, inspect it before composing the prompt and include in the prompt a relative source-location cue plus a readability note, such as whether the text is in the upper-left, centered header, or lower-right. Do not hardcode coordinates or inherit a name from a prior generation; if the source text is ambiguous, let the model choose. Use the cue only to help locate the source identity, then place the selected name inside module 1 with safe margins.
- When composing the generation prompt, do not force a name-length adjective or inject a fixed sample name. Ask for the full IP name to remain visible within its panel, with safe margins and automatic size/spacing adjustments if needed, while leaving the wording to the image model unless the user explicitly supplied a name.
- Keep the same person across the avatar, views, expressions, and actions: face geometry, hair silhouette, glasses or other stable facial feature, adult proportions when applicable, signature outfit, footwear, accessory, and palette must remain coherent.
- Let the current reference image establish appearance and let the current character-information brief establish the semantic world, outfit direction, tools, actions, and use cases. Let the model choose the character's gender expression, gestures, and exact pose when the user has not specified them.

## Do not turn the sheet into a poster

- Do not reproduce the source poster's contact details, long copy, logo, watermark, original layout, or decorative background.
- Do not add a second unrelated character, cinematic scene collage, interface chrome, dense biography, or large blocks of hard-to-read text.
- Do not inherit a previous character from the conversation. If the request says to ignore previous character information, treat that as a hard reset and use only the current visible reference image and current character-information brief.

The exact counts in `personal-ip-demo.png` are examples, not a rigid checklist: preserve all seven modules and the sheet's function while allowing the model to choose the most readable number of views, expressions, actions, anchors, and colors.
