# Prompt Template

Generate each image separately. For a series, first create an ordered shot list, then generate and save every shot one at a time. Never combine the series into a collage, and never stop after the first successful shot.

Before composing the final prompt:

- If the customer indicated that a personal-IP template should be used, obtain the template image — already attached this run, or ask the customer to attach it or point to a local file — and load it into context with `view_image` if it is a local file not already visible in context.
- If multiple customer-explicit candidates could be the template, stop and ask the customer which one to use.
- If no customer-explicit template was supplied at all, use the Xiaohei fallback branch.
- Once obtained, reuse that same template image across every shot in this run.
- If a customer-explicit template was indicated but no usable template image can be obtained, stop and report the blocker instead of falling back.

Set `{PERSONAL_IP_BRANCH}` to exactly one of these prompt fragments before submitting the prompt to `image_gen`:

- `Use the attached personal IP template as the recurring character reference. Keep the same identity, illustration language/style, and signature palette; place this character in the core conceptual action.`
- `No personal IP template was supplied for this request. Use the original Xiaohei character from xiaohei-ip.md as the recurring character: a solid-black absurd creature with white dot eyes, tiny thin legs, a blank serious expression, and a slightly uneven hand-drawn body.`

Do not reproduce a reference-sheet layout or invent a substitute character sheet.

```text
Generate one standalone 16:9 horizontal article illustration. Use the customer's requested language only for visible labels when labels are needed.

Visual DNA:
Pure white background. Minimalist hand-drawn line art. Slightly wobbly pen lines. Lots of empty white space. Sparse red/orange/blue handwritten annotations in the user's requested language when needed, or no text when labels are unnecessary. Clean absurd product-sketch feeling. No gradients, no shadows, no paper texture, no complex background, no commercial vector style, no PPT infographic look, no cute mascot poster, no children's illustration, no realistic UI.

Recurring character branch:
{PERSONAL_IP_BRANCH}

Theme:
{article illustration theme}

Structure type:
{structure type: workflow / system slice / before-after / state change / conceptual metaphor / layered method / route map / small comic beat}

Core idea:
{core idea}

Composition:
{specific scene: where the recurring character is, what it is doing, what the main object is, and how information or action flows}

Suggested elements:
{element 1} / {element 2} / {element 3} / {element 4}

Handwritten labels in the customer's requested language:
{label 1} / {label 2} / {label 3} / {label 4} / {optional label 5}

Color use:
Black for the main line art, scene structure, and text. Preserve the recurring character's signature palette when a customer template is used; use black for the character only in the Xiaohei fallback branch. Orange for the main flow, path, or arrows. Red only for key warnings, problems, or results. Blue only for secondary notes, feedback, or system state.

Constraints:
Each image explains only one core structure. Keep the main subject around 40%-60% of the canvas. Preserve at least 35% blank white space. Use at most 5-8 short handwritten labels in the customer's requested language, or omit labels when they are not necessary. Do not write a title in the top-left corner. Do not write the structure type on the image. Do not make it a formal diagram, course slide, or dense explainer. Do not copy prior examples or reuse known case compositions unless explicitly requested; invent a fresh visual metaphor for this specific article. Preserve the recurring character's identity, illustration language/style, and signature palette when a customer template is used; do not recolor that character to black. The black-character rule applies only to the Xiaohei fallback. It should be clear but not instructional, interesting but not childish, strange but clean. In a series, return separate image files in shot-list order, never a multi-panel collage.
```

## Edit Prompt

```text
Edit the provided image. Remove only the handwritten title "{text to remove}" and its underline from the top-left corner. Fill that area with the same clean white background, matching the surrounding blank paper. Preserve everything else exactly: characters, labels, paths, line style, composition, aspect ratio, and image quality. Do not add any new text or objects.
```

## Regeneration Prompt

```text
Regenerate this illustration with the same core meaning and simple layout, but make the recurring character more central to the conceptual action. The character should be doing the strange work that explains the idea, not standing beside the diagram. Keep it clean, sparse, hand-drawn, deadpan, and not cute.
```
