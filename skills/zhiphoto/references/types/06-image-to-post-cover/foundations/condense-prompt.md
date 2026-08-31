# Condensation Prompt

The second of the type's three reasoning steps: the fixed set of rules the agent applies itself to condense the extracted text (from the extraction step, or the customer's pasted words in the no-readable-text recovery path) into the four fields below.

Preserve the prompt below byte-for-byte, including the first line's mixed bracket pair `[detected words】`, the word 收成, and all punctuation. Do not "fix", rephrase, or translate anything in it.

```text
把下面[detected words】收成出图字段，只输出四行，不要解释：
主句：
收束：
画面：
光线：

规则：主句6-10字；收束一行，没有就写无；画面用一句话写清主体和地点，必须能解释主句，不要默认山水日落；光线只写一种。不要把故事段落写进主句。

原文：
[detected words]
```

## Filling rules

- **Substitution:** only the final `[detected words]` after `原文：` is replaced, with the agent's own extracted words verbatim (or, in the no-readable-text recovery path, the customer's pasted words). The first-line token `[detected words】` is part of the instruction sentence ("condense the detected words below") and stays literal.
- This step needs no new attachment or re-viewing of the image — it reasons only over the substitution above, the words already extracted (or pasted) in the previous step.

## Checking the condensation

- **Expected output shape:** exactly four lines, `主句：` `收束：` `画面：` `光线：`, no explanation. Check the agent's own condensed output against the rules above — 主句 is 6–10 characters; 收束 is one line or the literal 无; 画面 is one sentence naming subject and place that explains the 主句 (no default 山水日落); 光线 names exactly one lighting condition.
- If the agent's own condensed output does not come back as exactly four lines matching that shape, redo the condensation once more (at most one retry) rather than inventing or editing field values. If it still fails, stop and report the malformed result.
- The condensed four lines are not a customer confirmation gate: proceed to generation immediately once they pass the check above, then report them (and the extracted words) in the completion report and the prompt sidecar.
