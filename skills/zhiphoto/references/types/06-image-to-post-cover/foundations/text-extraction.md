# Main-Section Text Extraction

Applied by the agent itself when reading the source image, after `view_image` has brought it into context — the first of the type's three reasoning steps. The extracted words feed condensation (`condense-prompt.md`) next.

Unlike the fixed rules in `condense-prompt.md` and the fixed template in `cover-prompt.md`, this step has no byte-for-byte script — the agent applies judgment when reading the image — but it must always apply exactly the criteria described below.

## What counts as main-section text

When reading the viewed image, identify:

1. **The main section only** — the block(s) of text set in markedly larger and/or heavier type than everything else, typically in the central band (as a working threshold, roughly 1.5× the header/footer type height). Include a directly subordinate line that visibly completes the main statement (a paired subtitle); exclude small-type body paragraphs.
2. **Excluding functional strips** — header (top-edge app chrome, status bar, navigation, account name/avatar, timestamps, page title-bars) and footer (bottom-edge engagement counts, hashtags, CTAs, links, page numbers, disclaimers). A strip is functional by *content* (chrome/metadata/furniture), not merely by touching an edge — a huge poster headline at the very top is main-section text, not a header.
3. **Excluding brands everywhere** — logos, wordmarks, app names, watermarks, and @-handles, wherever they appear, including inside the main area.
4. **Read verbatim, in reading order** — the words exactly as written, in natural reading order, preserving the original language(s); no translation, correction, paraphrase, or added commentary.
5. **Say so plainly if nothing qualifies** — when the central content has no size hierarchy but is short (≲100 characters, e.g. a quote card or text-message screenshot), treat the whole block as the main section; when it's long and uniform, or no readable text exists in the main area at all, conclude that no clear main-section text was found rather than guessing.

## Extraction criteria, restated compactly

The paragraph below states the same five rules compactly, in Chinese, as a self-check the agent can hold while reading the image — it is a criteria checklist, not text to submit anywhere:

```text
请仅识别这张图片主体区域的文字：字号明显大于周围文字、通常位于视觉最突出位置的那部分内容。忽略页眉（顶部应用界面、状态栏、导航栏、账号名/头像、时间戳、页面标题）、页脚（底部互动数据、话题标签、按钮、链接、页码、免责声明），以及出现在图片任意位置的logo、水印、应用名和@账号。按原文顺序逐字识别文字，保留原语言，不要翻译、不要改写、不要加解释。如果主体区域没有可辨认的文字，视为未识别到主体文字。
```

## Recording the extraction

- Treat what was read as the extracted words verbatim — do not further edit, translate, or correct them; condensation owns compression.
- When the extracted words are partly or wholly non-Chinese, still use them as-is; condensation renders the four fields in Chinese regardless, and the completion report notes that the cover text is a Chinese condensation of non-Chinese source words. No confirmation gate for this — it is inherent in the type's fixed prompts, not a choice.
- When no readable main-section text is found (or the image is otherwise unusable for extraction — for example the main area holds a scene with no quotable text), follow the no-readable-text recovery path in `TYPE.md`.
- When several candidate text blocks are found with no clear primary one, follow the ambiguous-main-section path in `TYPE.md`.
- Record the extracted words verbatim in the completion report and the prompt sidecar's Provenance section, so extraction is auditable after the fact.
