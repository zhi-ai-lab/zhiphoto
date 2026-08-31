# Post Cover Language

Shared contract for every `ip-based-post-cover` profile. Profiles apply their deltas on top of this file; nothing here is optional.

## Inputs and output

- Two inputs per request: the customer's **character reference sheet** (obtained per `SKILL.md`'s **Resolve reference handling** — already attached this run, or the customer supplies one — then loaded into context with `view_image` before being passed to `image_gen`) and **"this episode in one sentence"** — one sentence, in the customer's own words, stating what this post or video says. Example: 独立开发者用 skill 把周更从熬夜改成定时发出去.
- Output is exactly **1 image**, **3:4 vertical**, sized for a two-column phone feed: few words, thick type, main line readable in one glance at thumbnail size.
- Think, then draw: read the sentence first and compose from it. The **character acts out the line, not the tool** — show the person doing or embodying the sentence, never a diagram of the method. The method appears only as a small tag.

## Character fidelity

- Strictly copy the same character from the reference sheet: face, hair, glasses, beard, clothes, body, line quality, and style.
- No face swap, no photorealism, no new character, no person who is not on the sheet.
- Clothes follow the sheet.

## Palette

Use only these colors: `#111111` `#2E2E2E` `#666666` `#F5C99A` `#FFFFFF` `#F5F5F5` `#F6A609`.

- Background: `#FFFFFF` or `#F5F5F5`.
- Accent: only `#F6A609`.

## Three copy lines

The cover carries exactly three text roles. Chinese must be correct. Never print the role names themselves ("main line", "audience line", "method line" or their Chinese equivalents) on the image — they are instructions, not copy.

- **Main line**: states the point. Extra-bold Chinese sans, the largest type on the image.
- **Audience line**: who this is for. About one-third the main line size.
- **Method line**: one short tag naming the method; may use `#F6A609`; stays clearly smaller than the main line.

## Composition bans

These hold for every profile:

- No flowcharts, no checklists, no footer process row or timeline.
- No prompt labels printed on the image.
- No watermark, no phone-app chrome.
