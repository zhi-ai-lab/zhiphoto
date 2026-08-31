# Cover Generation Prompt

This is the final `image_gen` call — the only step that actually generates an image, and the only step the transport's pre-generation confirmation gate and generation-time verification apply to. The four fields are filled from the agent's own condensation (the previous step). No new attachment accompanies this call, and the prompt itself makes no reference to the source image or to the extraction/condensation steps — only the four condensed field values drive the cover.

Preserve the prompt below byte-for-byte. Do not "fix", rephrase, or translate anything in it.

```text
出一张小红书3:4封面并保存到本地。
主句：
收束：
画面：
光线：
根据原意自己决定场景、物件、天气、光线，以及要不要人。人物只许背影、远景或侧影，不要正脸特写。不要默认木桌、湖、山、日落。每次换一套和原意有关的现场。
图上只许两行中文：「主句」最大，「收束」次之；收束为无则只留主句。字放在干净留白处，缩略图也能看清。写实摄影。无水印、无logo、无英文、不要再写其他字。
```

## Filling rules

- Append each condensed value, from the agent's own condensation, after its colon on the four field lines (主句/收束/画面/光线). **All four lines are always filled** — when there is no 收束, write the literal 无 (see the 收束=无 flow-through below).
- The composed prompt is the verbatim template with the four values filled and **nothing else** — no preamble, no appended instructions, no aspect-ratio restatement, no restatement of the source image or of the extraction/condensation steps. Added text is the main risk to a tuned prompt. The transport's requirements are already satisfied by the template itself (出一张 = one image; 3:4 = the aspect).
- `并保存到本地` stays in the prompt (verbatim rule). The image model cannot save to the customer's disk itself; the transport's export/verify steps perform the actual save, and whatever the model's own output says about saving is ignored.

## The 收束=无 flow-through

The condensation prompt outputs 无 when there is no closing line; the generation prompt's own rule 收束为无则只留主句 converts that into a one-line cover. So the pipeline rule is simply: **never drop the 收束： line from the template; fill it with 无 and let the prompt's built-in rule do the collapse.** Deleting the line would alter the verbatim template and orphan the 收束为无 rule.

## Verification

The exported cover must show exactly **one** line of Chinese (the 主句) when 收束 is 无, exactly **two** otherwise, with the 主句 visibly largest; the rendered characters must match the condensed fields. Garbled or wrong Chinese is a verification failure — report it per `references/transport/codex-image-gen.md`'s artifact verification section rather than treating the run as complete.
