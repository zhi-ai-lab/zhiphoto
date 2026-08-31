# ZhiPhoto Eval Suite

Runnable acceptance checks for a ZhiPhoto install. Any user can run them to confirm the
skill routes, generates, saves, and verifies correctly on their machine. The cases contain
no personal information; where a reference image matters, the case uses the fixed eval
reference bundle or the built-in Xiaohei fallback.

Each file in `eval/cases/` contains only the user-facing prompt for that case. Execution,
reference handling, artifact layout, and reporting rules live in [`eval/eval.md`](eval.md),
not in the case prompt.

## How to run

Paste the prompt in [`eval/test-start-prompt.md`](test-start-prompt.md) to kick off a full
automated run. [`eval/eval.md`](eval.md) is the actual runbook the agent follows — case
discovery order, the fixed reference bundle at
`/Volumes/T7-APFS/Development/zhiphoto/.local/eval/`, case 01b's dependency on case 01,
unattended execution, one-attempt policy, output layout, and report format are all defined
there. Generation uses Codex's built-in `image_gen` transport.

The suite may use up to three fresh Luna (`xhigh`) subagents in parallel, with one fresh
subagent per independent generation; case 01b stays in case 01's session. The agent checks
only route/transport and artifact integrity, while visual and content acceptance remains a
human review. The completed `.tmp/eval-<timestamp>/` folder is retained for audit and is not
automatically cleaned.

## Cases

| Case | Category | What it proves |
| --- | --- | --- |
| [01-general](cases/01-general.md) | general | fallback routing + plain generation |
| [01b-modification](cases/01b-modification.md) | (follows 01) | same-session modification + drift report |
| [02-window-light-portrait](cases/02-window-light-portrait.md) | portrait | scene routing + realistic portrait quality |
| [03-illustration](cases/03-illustration.md) | illustration | illustration routing + Xiaohei fallback (no reference) |
| [03b-illustration-with-reference](cases/03b-illustration-with-reference.md) | illustration | illustration routing + required template handling (with reference) |
| [05-ip-based-post-cover](cases/05-ip-based-post-cover.md) | illustration | required-reference handling (no fallback) + cover copy/palette rules |
| [06-image-to-post-cover](cases/06-image-to-post-cover.md) | general | text-source handling + self-applied extract/condense/generate flow |
| [07-image-to-image](cases/07-image-to-image.md) | general | visual-source handling + take/invent/exclude profile contract |
| [08-selfie](cases/08-selfie.md) | portrait | generation-only |
| [09-candid-car-flash-photo](cases/09-candid-car-flash-photo.md) | portrait | generation-only |
| [10-personal-ip](cases/10-personal-ip.md) | portrait | generation-only |
| [11-realistic-human-photo](cases/11-realistic-human-photo.md) | portrait | generation-only |

## Scoring

The agent reports `COMPLETED`, `FAILED`, or `SKIPPED` based on the mechanical execution and
artifact rules in `eval/eval.md`. The current case files have no inline checklists; visual
and content acceptance remains a separate human review. Images that complete may be reviewed
by a human and optionally promoted into `demo/` to serve as the project's demo set.
