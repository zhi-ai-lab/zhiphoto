# Identity Extraction and Lock

## Goal

Distill the person in the current supplied reference image into a simple visual identity that another image model can reproduce across many future scenes. The output should feel deliberately designed, not like a detailed cartoon copy of one photograph. The current attachment is mandatory for the reference-led workflow; do not replace it with a previous upload or with text-only invention.

## Source hierarchy

Apply these sources in order:

1. The current reference image defines who the person looks like.
2. The current character-information brief defines the role, personality, outfit direction, tools, actions, and intended character world.
3. The selected profile and its format reference define the output structure and visual simplification.
4. A future scene prompt defines what the established character is doing.

Previous prompts, previous uploaded images, and previous generated characters are not identity sources. If the user says to ignore previous character information, treat that as a hard reset: use only the current visible reference and current brief.

Do not infer occupation, personality, expertise, lifestyle, or permanent costume from the photo. Photo clothing, props, background, captions, and layout are temporary unless the user explicitly promotes them into the character specification.

## Read the reference correctly

Treat stable visible appearance as a strong constraint. Extract approximately four to six identity anchors, such as:

- hair silhouette or hairline
- face silhouette and broad feature relationships
- glasses, facial hair, or distinctive headwear when visible
- a characteristic smile or resting expression
- one or two other features that remain useful after simplification

Treat apparent age as a weak constraint: preserve an adult age impression without attempting exact age reconstruction. Do not infer sensitive traits that are not needed for the requested visual.

If the reference is a poster, social screenshot, or image with text, use the person as the reference subject and ignore the copy, layout, logos, scenery, and decorative treatment unless the user explicitly requests them. Character information supplied in the current prompt may define the semantic role, but it does not override the person's visible identity. Do not reproduce readable poster text, contact details, or logos inside the generated image by default.

When a personal-IP request needs an IP name and the source is a poster or screenshot, make a separate source-text cue scan before composing the prompt. Look for a clearly readable IP name, handle, profile name, or title; note its relative location in the source image (for example, upper-left, centered in a header, or lower-right) and whether the reading is unambiguous. Include that location cue in the image-generation prompt so the model can find the intended text across different screenshot layouts. Use the source name only when it is clearly the intended IP name or the user asks to preserve it; otherwise let the image model choose. The source location is a reading aid, not the output placement: the selected name still belongs inside output module 1 with safe margins. Do not copy unrelated poster copy, contact details, or logos.

Never hard-code a person's gender, age, race, face, hair, glasses, clothing, pose, or palette from an earlier prompt. Let the current image establish visible traits; when a trait is ambiguous, keep the design coherent without pretending to know more than the image supports.

## Convert identity into a simple character

Prioritize recognizability, consistency, simplicity, and extensibility over decoration.

- Build the character from roughly four to seven large, rounded shapes.
- Use a clear adult silhouette with natural simplified proportions; do not turn a human subject into a baby-like chibi character.
- Preserve the paired features that carry recognition, such as both glasses lenses or both ears.
- Use thick rounded contours, flat color masses, restrained shading, and very little texture.
- Remove small lines, repeated details, realistic fabric texture, dramatic lighting, and decorative background elements.
- For the canonical mark, use two purposeful character color families plus one clearly separated background color unless the user specifies another palette.

## Semantic character design

The user's text, not the reference photo, controls the semantic design. Let the stated role determine canonical clothing, authentic tools, professional actions, and environment. Do not add generic creator props such as laptops, coffee cups, microphones, or light bulbs unless the brief makes them relevant.

If the current brief is missing a role or other detail that materially changes the result, ask one consolidated clarification round. Otherwise make the smallest reasonable assumption and keep it easy to override. The model should determine the exact character, gestures, action poses, and temporary props — informed by what the reference image itself shows or states, including any visible text, caption, or label on it — unless the user has explicitly fixed them. Do not pre-enumerate specific action poses in the composed prompt; describe the character-information brief's role and world, and instruct the image model to invent role-appropriate poses itself.

## Identity lock

Once a canonical design is established, preserve the same face geometry, hairstyle, glasses or facial hair, signature accessory, approximate adult age, body proportions, canonical outfit, palette, and illustration language. Future prompts may change pose, expression, action, scene, and temporary props; they must not silently redesign the person.

The canonical character sheet, when approved, becomes the primary visual reference for later scene generation. Do not restart from the original photo for every new scene. The sheet's format reference is not a second character reference: use it for layout only.

## Prompt boundary

The surrounding workflow may call this a personal IP or logo project, but the image-generation prompt should describe only the requested visual. Do not tell the image model that it is making a logo, brand mark, app icon, or icon asset. Keep the prompt focused on the character, composition, color, and constraints.

Generated images are stochastic creative draws. Preserve the returned result and let the user request refinements explicitly; do not automatically rank, reject, repair, or retry it because of subjective style differences.
