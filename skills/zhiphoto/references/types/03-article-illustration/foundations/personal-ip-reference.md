# Personal IP Reference Resolution

Prefer a customer-explicit personal-IP template for the recurring character in this type, and use Xiaohei only when the customer supplied no template intent at all.

## Resolution order

1. Check whether the customer indicated that a personal-IP template should be used for this request, such as by referring to a template attachment or naming one in the request.
2. If template intent exists and multiple candidate templates are plausible, stop and ask the customer which one to use.
3. If template intent exists, obtain the template image — already attached this run, or ask the customer to attach it or point to a local file — and load it into context with `view_image` if it is a local file not already visible in context.
4. Use that image as the reference for every shot in this run. Preserve its stable identity anchors, such as silhouette, face geometry, signature accessories, age-appropriate proportions, and illustration language, while changing only the pose, action, temporary props, and scene needed by the article brief. Do not reproduce the character sheet layout or its labels.
5. If template intent exists but no usable template image can be obtained, stop and report the blocker. Do not fall back.
6. If no template intent exists, use the original Xiaohei fallback from `xiaohei-ip.md`.

## Prompt contract

The final prompt must state which branch was selected:

- Template supplied by the customer for this run: `Use the attached personal IP template as the recurring character reference. Keep the same identity and illustration language; place this character in the core conceptual action.`
- No template supplied: `No personal IP template was supplied for this request. Use the original Xiaohei character from xiaohei-ip.md as the recurring character: a solid-black absurd creature with white dot eyes, tiny thin legs, a blank serious expression, and a slightly uneven hand-drawn body.`

The reference image controls identity only. The article brief controls the role, action, scene, and conceptual meaning. Never infer a permanent occupation, personality, or costume from unrelated visual details in the template.
