# Releasing this repository

Releases of every `zhi-ai-lab` `zhi*` repository are cut with the Codex skill
**`zhirelease`**. Invoke `$zhirelease` from a Codex session in this repository. The
`dev` → `main` merge is the release: the skill runs the documented checks, opens a
GitHub pull request, stops once for the maintainer's “ship” approval, then merges the
PR server-side and creates the GitHub Release from the merge commit.

The local checkout remains on `dev` throughout. The skill never checks out `main`,
locally pushes `main`, or locally creates release tags.
