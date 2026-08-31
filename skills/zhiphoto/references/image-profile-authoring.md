# Image Type and Profile Authoring Contract

Add a specialized image type under `references/types/<type-id>/`. Catalog discovery is automatic: do not edit `SKILL.md` or `scripts/image_catalog.py` to register identifiers.

## Type record

Create `TYPE.md` directly under the type folder with exactly this `image-type/v2` frontmatter shape:

```yaml
---
schema: image-type/v2
type_version: 1
id: lowercase-hyphenated-type-id
title: Human-readable type title
summary: One sentence distinguishing when the type applies.
keywords: ["search phrase", "another phrase", "中文关键词"]
category: general
profile_kind: scene
fallback: false
required_refs: ["references/types/lowercase-hyphenated-type-id/foundations/shared-guidance.md"]
reference_policy: optional
reference_role: likeness
sort_order: 30
---
```

The folder name must equal `id`. `type_version` must be positive. `profile_kind` is a lowercase hyphenated category shared by every profile in the type — it describes each profile's *structural role* within the type (for example `scene` for a situational variant, `look` for a visual-treatment variant, `identity` for a character-identity variant, `mode` for a generic fallback mode). `fallback` is an unquoted boolean, and exactly one type across the catalog must be the fallback. Required references must be non-empty, existing regular files inside that type's folder; absolute paths, traversal, and symlink escapes are rejected. `schema: image-type/v1` is rejected outright with an error naming the missing fields — there is no silent upgrade path.

`category` is one of exactly `general`, `portrait`, or `illustration`. It is a routing/grouping label only; directories stay flat regardless of category. These are default IDs Jason can rename later — they are not architecturally load-bearing beyond `list-types --grouped` and `route`'s `category` field in each candidate.

`reference_policy` is one of exactly `required` or `optional` — whether this type needs a customer-supplied reference image to run at all. `reference_role` is a lowercase-hyphenated slug describing what a supplied reference *means* for this type (validated as a slug, not a closed enum, so new roles can be introduced without a script change); the catalog's current values are `identity-source` (personal-ip: the reference establishes the character's visible identity), `recurring-template` (article-illustration and ip-based-post-cover: the reference is a recurring character template, with the built-in Xiaohei illustration as the fallback when none is supplied for article-illustration), `likeness` (every photo/general type: an optional reference improves consistency but is never required), `text-source` (image-to-post-cover: the reference supplies its words, read by the agent loading the image directly and passing it to `image_gen`), and `visual-source` (image-to-image: the reference supplies visuals — style, subject, mood, composition — with the selected profile fixing which of those are taken; loaded by the agent directly and passed to `image_gen`, not through any web checkpoint).

Two further optional keys exist for the identity-template relationship: a type that manufactures a reusable identity template declares `produces: identity-template` (personal-ip does this); a type that consumes one as its reference declares `consumes: identity-template` (article-illustration does this). Both are plain slug strings, omitted entirely from every other type's frontmatter — do not add empty/null placeholders for types that neither produce nor consume one.

Every type inherits the transport's artifact contract: each generated image is saved together with its final composed prompt in a `<basename>.prompt.md` sidecar (see `references/transport/codex-image-gen.md`, "File naming and artifact verification"). A new type's `TYPE.md` body should carry the standard pointer line used across the catalog: "Every run of this type saves its final composed prompt beside the exported image, per the transport artifact contract in `references/transport/codex-image-gen.md` (File naming and artifact verification)."

## Profile record

Place one or more Markdown files under `references/types/<type-id>/profiles/`, including nested folders when useful. Use exactly this `image-profile/v1` frontmatter shape:

```yaml
---
schema: image-profile/v1
profile_version: 1
id: lowercase-hyphenated-profile-id
type: lowercase-hyphenated-type-id
kind: scene
title: Human-readable profile title
summary: One sentence distinguishing when the profile applies.
keywords: ["search phrase", "another phrase"]
maturity: general
adult_only: false
sort_order: 10
---
```

The filename stem must equal `id`, the profile's `type` must equal its container folder, and `kind` must equal the type's `profile_kind`. Profile IDs must be unique within their type; different types may reuse an ID such as `direct`. `profile_version` must be positive. `maturity` is `general` or `adult`; `adult_only` must be the unquoted boolean `false` for general profiles and `true` for adult profiles.

Use this body shape and write only deltas from the type's required references:

```markdown
# Human-readable profile title

## Use When

Selection boundary.

## Profile Deltas

- Profile-specific direction.

## Profile-Specific Avoidances

- Profile-specific likely failure mode.
```

Keyword and required-reference lists use non-empty JSON string-array syntax without duplicates. Write keywords bilingually where the type or profile is meaningfully searched in both languages — pair an English phrase with its natural Chinese phrasing rather than a literal translation, since `route` matches Chinese keywords by character overlap and English keywords by whole-phrase word-boundary match. Sort orders are non-negative; ties among profiles are allowed and resolve deterministically by ID. Sort orders across **types** must be pairwise unique — `validate` fails on a collision — since router candidate ordering also uses `(type.sort_order, type.id)` as its tie-break key.

## Validate

```bash
python3 scripts/image_catalog.py validate
python3 scripts/image_catalog.py list-types --format json
python3 scripts/image_catalog.py list-types --grouped --format json
python3 scripts/image_catalog.py list-profiles --type <type-id> --format json
python3 scripts/image_catalog.py resolve --type <type-id> --profile <profile-id> --format json
python3 scripts/image_catalog.py route --brief "<free-text request>" --has-reference yes|no --format json
```

`validate` enforces: schema is exactly `image-type/v2`; `category` is one of the allowed set; `reference_policy` and `reference_role` are present and valid; keywords are non-empty; type ids are unique; type `sort_order` values are unique across the whole catalog; and it warns (without failing) when two profiles anywhere in the catalog declare an identical keyword string, since that collision weakens `route`'s discriminating power between them.

`list-types --grouped` returns `{category: [type entries]}` instead of a flat list — the same type records, just partitioned by `category` and internally still ordered by `(sort_order, id)`.

`route --brief "<text>" [--has-reference yes|no]` scores every (type, profile) pair deterministically from the type's and profile's own title/keywords and returns the top candidates, each carrying `type`, `profile`, `score`, `category`, `reference_policy`, and `matched_terms`. `--has-reference yes` boosts any type whose `reference_policy` is `required`; `--has-reference no` strongly demotes `personal-ip` specifically (it cannot run without a reference) without touching `article-illustration` (it has the Xiaohei fallback). No network access and no third-party dependencies — matching is pure stdlib string/regex logic.
