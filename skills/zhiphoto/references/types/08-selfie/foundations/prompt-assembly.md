# Prompt Assembly

Build one coherent generation prompt in this order.

## 1. Preserve the request

Start with the user's subject, clearly adult age when relevant, action, expression, styling, setting, and intended mood. Keep stated identity traits and lighting directions exact. Do not introduce ethnicity, body shape, clothing exposure, or sexual intensity the user did not request.

## 2. Add the selected scene delta

Translate the selected scene's directives into concrete visual language. Use its defaults only to fill gaps; the user's explicit choices take priority. Include only the few details that materially establish the scene.

## 3. Add shared realism

Incorporate the useful capture geometry, anatomy, texture, lighting, and phone-camera behavior from `selfie-realism.md`. Avoid a long checklist: choose details that explain the requested image.

## 4. Add modifiers conditionally

If identity continuity is needed, append the constraints from `../modifiers/identity-continuity.md`. Keep modifiers independent of the selected scene.

## 5. Finish with focused avoidances

Include only failure modes likely for this prompt, including scene-specific avoidances. Prefer positive, visual direction over a generic negative-prompt dump.

## Output contract

Return a ready-to-generate prompt, plus concise aspect-ratio or framing guidance when useful. Do not include browser steps, download instructions, local paths, generation-tool parameters, or private source provenance. Those belong to the generation transport skill.
