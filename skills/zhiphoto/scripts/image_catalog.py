#!/usr/bin/env python3
"""Discover, resolve, and validate generic image types and profiles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TYPE_SCHEMA = "image-type/v2"
TYPE_SCHEMA_LEGACY_V1 = "image-type/v1"
PROFILE_SCHEMA = "image-profile/v1"
TYPE_REQUIRED_KEYS = {
    "schema",
    "type_version",
    "id",
    "title",
    "summary",
    "keywords",
    "profile_kind",
    "fallback",
    "required_refs",
    "sort_order",
    "category",
    "reference_policy",
    "reference_role",
}
TYPE_OPTIONAL_KEYS = {"produces", "consumes"}
PROFILE_KEYS = {
    "schema",
    "profile_version",
    "id",
    "type",
    "kind",
    "title",
    "summary",
    "keywords",
    "maturity",
    "adult_only",
    "sort_order",
}
MATURITY_VALUES = {"general", "adult"}
CATEGORY_VALUES = {"general", "portrait", "illustration"}
REFERENCE_POLICY_VALUES = {"required", "optional"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CJK_PATTERN = re.compile(r"[一-鿿㐀-䶿]")
ASCII_WORD_PATTERN = re.compile(r"[a-z0-9']+")
# Keyword/title match weights, split by how well the phrase matched. A "contiguous"
# match is the phrase's exact word sequence found as one run in the brief (or, for a
# single-word phrase / a CJK phrase, simply "found" — those have no partial tier). A
# "partial" match is a multi-word ASCII phrase whose words all appear somewhere in the
# brief, in any order, not necessarily adjacent. Partial always scores lower than
# contiguous so an exact phrasing still outranks a scattered one.
KEYWORD_CONTIGUOUS_WEIGHT = 3
KEYWORD_PARTIAL_WEIGHT = 2
TITLE_CONTIGUOUS_WEIGHT = 2
TITLE_PARTIAL_WEIGHT = 1
REFERENCE_REQUIRED_BONUS = 4
NO_REFERENCE_PERSONAL_IP_PENALTY = 100
ROUTE_CANDIDATE_LIMIT = 5
SKILL_ROOT = Path(__file__).resolve().parent.parent
TYPES_DIR = SKILL_ROOT / "references" / "types"


class CatalogError(ValueError):
    """The image catalog is malformed or cannot resolve a requested record."""


@dataclass(frozen=True)
class ImageType:
    schema: str
    type_version: int
    id: str
    title: str
    summary: str
    keywords: tuple[str, ...]
    profile_kind: str
    fallback: bool
    required_refs: tuple[str, ...]
    required_ref_paths: tuple[Path, ...]
    sort_order: int
    category: str
    reference_policy: str
    reference_role: str
    path: Path
    produces: str | None = None
    consumes: str | None = None

    def public_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "type_version": self.type_version,
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "keywords": list(self.keywords),
            "profile_kind": self.profile_kind,
            "fallback": self.fallback,
            "required_refs": list(self.required_refs),
            "sort_order": self.sort_order,
            "category": self.category,
            "reference_policy": self.reference_policy,
            "reference_role": self.reference_role,
            "produces": self.produces,
            "consumes": self.consumes,
            "path": _relative_path(self.path),
        }


@dataclass(frozen=True)
class ImageProfile:
    schema: str
    profile_version: int
    id: str
    type: str
    kind: str
    title: str
    summary: str
    keywords: tuple[str, ...]
    maturity: str
    adult_only: bool
    sort_order: int
    path: Path

    def public_record(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "profile_version": self.profile_version,
            "id": self.id,
            "type": self.type,
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
            "keywords": list(self.keywords),
            "maturity": self.maturity,
            "adult_only": self.adult_only,
            "sort_order": self.sort_order,
            "path": _relative_path(self.path),
        }


@dataclass(frozen=True)
class Catalog:
    types: tuple[ImageType, ...]
    profiles: tuple[ImageProfile, ...]


def _relative_path(path: Path) -> str:
    return path.resolve().relative_to(SKILL_ROOT).as_posix()


def _parse_scalar(raw_value: str, *, path: Path, line_number: int) -> Any:
    value = raw_value.strip()
    if not value:
        raise CatalogError(f"{path}:{line_number}: empty values are not allowed")
    if value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise CatalogError(
                f"{path}:{line_number}: list values must use JSON string-array syntax"
            ) from exc
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?[0-9]+", value):
        return int(value)
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise CatalogError(f"{path}:{line_number}: invalid quoted string") from exc
    return value


def _read_frontmatter(path: Path) -> dict[str, Any]:
    """Read only the initial frontmatter block, never the Markdown body."""
    with path.open("r", encoding="utf-8") as handle:
        if handle.readline().rstrip("\r\n") != "---":
            raise CatalogError(f"{path}: frontmatter must begin on line 1")
        metadata: dict[str, Any] = {}
        for line_number, line in enumerate(handle, start=2):
            stripped = line.rstrip("\r\n")
            if stripped == "---":
                return metadata
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            if stripped[:1].isspace() or ":" not in stripped:
                raise CatalogError(
                    f"{path}:{line_number}: frontmatter must contain top-level key/value pairs"
                )
            key, raw_value = stripped.split(":", 1)
            key = key.strip()
            if not key or key in metadata:
                raise CatalogError(f"{path}:{line_number}: invalid or duplicate key {key!r}")
            metadata[key] = _parse_scalar(raw_value, path=path, line_number=line_number)
    raise CatalogError(f"{path}: frontmatter has no closing delimiter")


def _strict_keys(
    metadata: dict[str, Any],
    required: set[str],
    schema: str,
    path: Path,
    *,
    optional: frozenset[str] = frozenset(),
) -> None:
    actual = set(metadata)
    allowed = required | optional
    if actual == required or (actual >= required and actual <= allowed):
        return
    details = []
    missing = sorted(required - actual)
    extra = sorted(actual - allowed)
    if missing:
        details.append(f"missing {missing}")
    if extra:
        details.append(f"unknown {extra}")
    raise CatalogError(f"{path}: strict {schema} schema violation: {', '.join(details)}")


def _string(metadata: dict[str, Any], key: str, path: Path) -> str:
    value = metadata[key]
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{path}: {key!r} must be a non-empty string")
    return value.strip()


def _string_list(metadata: dict[str, Any], key: str, path: Path) -> tuple[str, ...]:
    value = metadata[key]
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise CatalogError(f"{path}: {key!r} must be a non-empty JSON array of strings")
    normalized = tuple(item.strip() for item in value)
    if len(set(normalized)) != len(normalized):
        raise CatalogError(f"{path}: {key!r} must not contain duplicates")
    return normalized


def _positive_integer(metadata: dict[str, Any], key: str, path: Path) -> int:
    value = metadata[key]
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CatalogError(f"{path}: {key!r} must be a positive integer")
    return value


def _sort_order(metadata: dict[str, Any], path: Path) -> int:
    value = metadata["sort_order"]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CatalogError(f"{path}: 'sort_order' must be a non-negative integer")
    return value


def _boolean(metadata: dict[str, Any], key: str, path: Path) -> bool:
    value = metadata[key]
    if not isinstance(value, bool):
        raise CatalogError(f"{path}: {key!r} must be the unquoted boolean true or false")
    return value


def _slug(value: str, key: str, path: Path) -> str:
    if not SLUG_PATTERN.fullmatch(value):
        raise CatalogError(f"{path}: {key!r} must be a lowercase hyphenated slug")
    return value


def _enum(value: str, key: str, allowed: set[str], path: Path) -> str:
    if value not in allowed:
        raise CatalogError(f"{path}: {key!r} must be one of {sorted(allowed)}")
    return value


def _is_cjk_phrase(phrase: str) -> bool:
    return bool(CJK_PATTERN.search(phrase))


def _cjk_bigrams(phrase: str) -> list[str]:
    chars = [char for char in phrase if not char.isspace()]
    if len(chars) <= 1:
        return ["".join(chars)] if chars else []
    return ["".join(chars[index : index + 2]) for index in range(len(chars) - 1)]


def _ascii_word_boundary_pattern(word: str) -> re.Pattern[str]:
    return re.compile(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])")


def _ascii_word_present(word: str, brief_casefold: str) -> bool:
    return _ascii_word_boundary_pattern(word).search(brief_casefold) is not None


def _phrase_match_score(
    phrase: str, brief_casefold: str, *, contiguous_weight: int, partial_weight: int
) -> int:
    """Score one keyword/title phrase against the casefolded routing brief.

    Chinese (CJK) phrases match by character-bigram substring overlap, since a short
    user brief will rarely repeat a curated multi-character phrase verbatim and
    Chinese has no whitespace word boundaries; a bigram hit scores `contiguous_weight`
    and there is no partial tier for CJK (unchanged from before this fix cycle).

    English/ASCII phrases first try a whole-phrase match: the phrase's exact word
    sequence found as one contiguous run in the brief, bounded on both sides by a
    non-alphanumeric character (or the brief's start/end) — this scores
    `contiguous_weight`. A single-word phrase only has this tier (there is nothing to
    be "partial" about one word), so it behaves exactly as before this fix cycle. A
    multi-word phrase that fails the contiguous check falls back to a partial check:
    it scores `partial_weight` when every one of its words is present as a
    whole-word, case-insensitive match somewhere in the brief, in any order and not
    necessarily adjacent — this catches natural phrasing like "candid photo inside a
    car" for the keyword "inside car", which no contiguous match would ever catch.
    Both branches match against the casefolded brief so a keyword mixing CJK and
    Latin characters (e.g. "真人IP") matches case-insensitively on its Latin portion
    too. Returns 0 when nothing matches.
    """
    phrase = phrase.strip()
    if not phrase:
        return 0
    if _is_cjk_phrase(phrase):
        matched = any(
            bigram and bigram in brief_casefold for bigram in _cjk_bigrams(phrase.casefold())
        )
        return contiguous_weight if matched else 0
    phrase_casefold = phrase.casefold()
    words = ASCII_WORD_PATTERN.findall(phrase_casefold)
    if not words:
        return 0
    if _ascii_word_boundary_pattern(phrase_casefold).search(brief_casefold) is not None:
        return contiguous_weight
    if len(words) == 1:
        return 0
    if all(_ascii_word_present(word, brief_casefold) for word in words):
        return partial_weight
    return 0


def _score_phrases(
    title: str, keywords: tuple[str, ...], brief_casefold: str
) -> tuple[int, list[str]]:
    score = 0
    matched: list[str] = []
    for keyword in keywords:
        contribution = _phrase_match_score(
            keyword,
            brief_casefold,
            contiguous_weight=KEYWORD_CONTIGUOUS_WEIGHT,
            partial_weight=KEYWORD_PARTIAL_WEIGHT,
        )
        if contribution:
            score += contribution
            matched.append(keyword)
    title_contribution = _phrase_match_score(
        title,
        brief_casefold,
        contiguous_weight=TITLE_CONTIGUOUS_WEIGHT,
        partial_weight=TITLE_PARTIAL_WEIGHT,
    )
    if title_contribution:
        score += title_contribution
        matched.append(title)
    return score, matched


def _resolve_required_refs(
    raw_refs: tuple[str, ...], *, type_directory: Path, record_path: Path
) -> tuple[Path, ...]:
    type_root = type_directory.resolve(strict=True)
    resolved_paths: list[Path] = []
    for raw_ref in raw_refs:
        relative = Path(raw_ref)
        if relative.is_absolute() or ".." in relative.parts:
            raise CatalogError(f"{record_path}: unsafe required_refs path {raw_ref!r}")
        candidate = SKILL_ROOT / relative
        try:
            candidate.absolute().relative_to(type_directory.absolute())
        except ValueError as exc:
            raise CatalogError(
                f"{record_path}: required_refs path must be inside {type_directory}"
            ) from exc
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise CatalogError(f"{record_path}: required reference not found: {raw_ref}") from exc
        try:
            resolved.relative_to(type_root)
        except ValueError as exc:
            raise CatalogError(
                f"{record_path}: required_refs symlink escapes its type folder: {raw_ref}"
            ) from exc
        if not resolved.is_file():
            raise CatalogError(f"{record_path}: required reference is not a regular file: {raw_ref}")
        resolved_paths.append(resolved)
    return tuple(resolved_paths)


def _load_type(path: Path) -> ImageType:
    metadata = _read_frontmatter(path)
    if metadata.get("schema") == TYPE_SCHEMA_LEGACY_V1:
        raise CatalogError(
            f"{path}: schema {TYPE_SCHEMA_LEGACY_V1!r} is no longer supported; upgrade this "
            f"TYPE.md to {TYPE_SCHEMA!r} by adding 'category', 'reference_policy', and "
            "'reference_role' (see references/image-profile-authoring.md)"
        )
    _strict_keys(metadata, TYPE_REQUIRED_KEYS, TYPE_SCHEMA, path, optional=frozenset(TYPE_OPTIONAL_KEYS))
    schema = _string(metadata, "schema", path)
    if schema != TYPE_SCHEMA:
        raise CatalogError(f"{path}: schema must be exactly {TYPE_SCHEMA!r}")
    type_id = _slug(_string(metadata, "id", path), "id", path)
    if path.parent.name != type_id:
        raise CatalogError(f"{path}: containing folder must match type id {type_id!r}")
    profile_kind = _slug(_string(metadata, "profile_kind", path), "profile_kind", path)
    required_refs = _string_list(metadata, "required_refs", path)
    resolved_refs = _resolve_required_refs(
        required_refs, type_directory=path.parent, record_path=path
    )
    category = _enum(_string(metadata, "category", path), "category", CATEGORY_VALUES, path)
    reference_policy = _enum(
        _string(metadata, "reference_policy", path),
        "reference_policy",
        REFERENCE_POLICY_VALUES,
        path,
    )
    reference_role = _slug(_string(metadata, "reference_role", path), "reference_role", path)
    produces = (
        _slug(_string(metadata, "produces", path), "produces", path)
        if "produces" in metadata
        else None
    )
    consumes = (
        _slug(_string(metadata, "consumes", path), "consumes", path)
        if "consumes" in metadata
        else None
    )
    return ImageType(
        schema=schema,
        type_version=_positive_integer(metadata, "type_version", path),
        id=type_id,
        title=_string(metadata, "title", path),
        summary=_string(metadata, "summary", path),
        keywords=_string_list(metadata, "keywords", path),
        profile_kind=profile_kind,
        fallback=_boolean(metadata, "fallback", path),
        required_refs=required_refs,
        required_ref_paths=resolved_refs,
        sort_order=_sort_order(metadata, path),
        category=category,
        reference_policy=reference_policy,
        reference_role=reference_role,
        produces=produces,
        consumes=consumes,
        path=path.resolve(),
    )


def _load_profile(path: Path, image_type: ImageType) -> ImageProfile:
    metadata = _read_frontmatter(path)
    _strict_keys(metadata, PROFILE_KEYS, PROFILE_SCHEMA, path)
    schema = _string(metadata, "schema", path)
    if schema != PROFILE_SCHEMA:
        raise CatalogError(f"{path}: schema must be exactly {PROFILE_SCHEMA!r}")
    profile_id = _slug(_string(metadata, "id", path), "id", path)
    if path.stem != profile_id:
        raise CatalogError(f"{path}: filename stem must match profile id {profile_id!r}")
    profile_type = _slug(_string(metadata, "type", path), "type", path)
    if profile_type != image_type.id:
        raise CatalogError(
            f"{path}: profile type {profile_type!r} must match container {image_type.id!r}"
        )
    kind = _slug(_string(metadata, "kind", path), "kind", path)
    if kind != image_type.profile_kind:
        raise CatalogError(
            f"{path}: profile kind {kind!r} must match type profile_kind "
            f"{image_type.profile_kind!r}"
        )
    maturity = _string(metadata, "maturity", path)
    if maturity not in MATURITY_VALUES:
        raise CatalogError(f"{path}: maturity must be one of {sorted(MATURITY_VALUES)}")
    adult_only = _boolean(metadata, "adult_only", path)
    expected_adult_only = maturity == "adult"
    if adult_only is not expected_adult_only:
        raise CatalogError(
            f"{path}: maturity {maturity!r} requires adult_only: "
            f"{str(expected_adult_only).lower()}"
        )
    return ImageProfile(
        schema=schema,
        profile_version=_positive_integer(metadata, "profile_version", path),
        id=profile_id,
        type=profile_type,
        kind=kind,
        title=_string(metadata, "title", path),
        summary=_string(metadata, "summary", path),
        keywords=_string_list(metadata, "keywords", path),
        maturity=maturity,
        adult_only=adult_only,
        sort_order=_sort_order(metadata, path),
        path=path.resolve(),
    )


def load_catalog() -> Catalog:
    if not TYPES_DIR.is_dir():
        raise CatalogError(f"type directory does not exist: {TYPES_DIR}")
    type_directories = sorted(path for path in TYPES_DIR.iterdir() if path.is_dir())
    if not type_directories:
        raise CatalogError(f"no type folders found in {TYPES_DIR}")

    image_types: list[ImageType] = []
    profiles: list[ImageProfile] = []
    for type_directory in type_directories:
        type_path = type_directory / "TYPE.md"
        if not type_path.is_file():
            raise CatalogError(f"type folder has no TYPE.md: {type_directory}")
        image_type = _load_type(type_path)
        image_types.append(image_type)
        profile_directory = type_directory / "profiles"
        if not profile_directory.is_dir():
            raise CatalogError(f"type folder has no profiles directory: {type_directory}")
        profile_paths = sorted(profile_directory.rglob("*.md"))
        if not profile_paths:
            raise CatalogError(f"type has no profiles: {image_type.id}")
        profiles.extend(
            _load_profile(profile_path, image_type)
            for profile_path in profile_paths
        )

    type_ids = [record.id for record in image_types]
    duplicate_types = sorted({item for item in type_ids if type_ids.count(item) > 1})
    if duplicate_types:
        raise CatalogError(f"duplicate type ids: {duplicate_types}")
    profile_ids = [(record.type, record.id) for record in profiles]
    duplicate_profiles = sorted(
        {item for item in profile_ids if profile_ids.count(item) > 1}
    )
    if duplicate_profiles:
        raise CatalogError(f"duplicate profile ids within types: {duplicate_profiles}")
    fallbacks = [record.id for record in image_types if record.fallback]
    if len(fallbacks) != 1:
        raise CatalogError(f"catalog must contain exactly one fallback type; found {fallbacks}")
    type_sort_orders = [record.sort_order for record in image_types]
    duplicate_sort_orders = sorted(
        {item for item in type_sort_orders if type_sort_orders.count(item) > 1}
    )
    if duplicate_sort_orders:
        raise CatalogError(f"duplicate sort_order across types: {duplicate_sort_orders}")

    return Catalog(
        types=tuple(sorted(image_types, key=lambda record: (record.sort_order, record.id))),
        profiles=tuple(sorted(profiles, key=lambda record: (record.sort_order, record.id))),
    )


def _profile_keyword_collision_warnings(catalog: Catalog) -> list[str]:
    """Warn (never fail) when two profiles declare an identical keyword string."""
    owners_by_keyword: dict[str, list[str]] = {}
    for profile in catalog.profiles:
        for keyword in profile.keywords:
            owners_by_keyword.setdefault(keyword, []).append(f"{profile.type}/{profile.id}")
    warnings = []
    for keyword, owners in sorted(owners_by_keyword.items()):
        if len(owners) > 1:
            warnings.append(f"keyword {keyword!r} shared by profiles: {', '.join(sorted(owners))}")
    return warnings


def _format_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("text", "json"), default="text")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    list_types = commands.add_parser("list-types", help="list image type metadata")
    list_types.add_argument(
        "--grouped", action="store_true", help="group types as {category: [type entries]}"
    )
    _format_option(list_types)
    list_profiles = commands.add_parser("list-profiles", help="list profiles for one type")
    list_profiles.add_argument("--type", required=True)
    _format_option(list_profiles)
    resolve = commands.add_parser("resolve", help="resolve type, required refs, and profile paths")
    resolve.add_argument("--type", required=True)
    resolve.add_argument("--profile")
    _format_option(resolve)
    route = commands.add_parser(
        "route", help="score type/profile candidates for a free-text brief"
    )
    route.add_argument("--brief", required=True)
    route.add_argument("--has-reference", choices=("yes", "no"), default=None)
    _format_option(route)
    commands.add_parser("validate", help="validate the complete catalog")
    return parser


def _type_by_id(catalog: Catalog, type_id: str) -> ImageType:
    matches = [record for record in catalog.types if record.id == type_id]
    if not matches:
        choices = ", ".join(record.id for record in catalog.types)
        raise CatalogError(f"unknown type id {type_id!r}; choose one of: {choices}")
    return matches[0]


def _profiles_for(catalog: Catalog, type_id: str) -> list[ImageProfile]:
    return [record for record in catalog.profiles if record.type == type_id]


def _emit_records(records: list[dict[str, Any]], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(records, indent=2, ensure_ascii=False))
        return
    for record in records:
        print(f"{record['id']}\t{record['title']}\t{record['summary']}")


def _grouped_types(catalog: Catalog) -> dict[str, list[dict[str, Any]]]:
    """Group type records by category, preserving each type's overall (sort_order, id) order."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for category in sorted(CATEGORY_VALUES):
        members = [
            record.public_record() for record in catalog.types if record.category == category
        ]
        if members:
            grouped[category] = members
    return grouped


def _emit_grouped_types(catalog: Catalog, output_format: str) -> None:
    grouped = _grouped_types(catalog)
    if output_format == "json":
        print(json.dumps(grouped, indent=2, ensure_ascii=False))
        return
    for category, members in grouped.items():
        print(f"## {category}")
        for record in members:
            print(f"{record['id']}\t{record['title']}\t{record['summary']}")


def route_candidates(
    catalog: Catalog, brief: str, has_reference: str | None
) -> list[dict[str, Any]]:
    """Score every (type, profile) pair against a free-text brief.

    Deterministic, stdlib-only keyword scoring: see `_phrase_match_score` for the
    bilingual, contiguous-vs-partial matching rule and the KEYWORD_CONTIGUOUS_WEIGHT /
    KEYWORD_PARTIAL_WEIGHT / TITLE_CONTIGUOUS_WEIGHT / TITLE_PARTIAL_WEIGHT /
    REFERENCE_REQUIRED_BONUS / NO_REFERENCE_PERSONAL_IP_PENALTY module constants for the
    exact weights. Ties break by (type.sort_order, type.id, profile.sort_order,
    profile.id). Always returns the top ROUTE_CANDIDATE_LIMIT candidates (or fewer only
    if the catalog has fewer pairs than that).
    """
    brief_casefold = brief.casefold()
    scored: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for image_type in catalog.types:
        type_score, type_matched = _score_phrases(
            image_type.title, image_type.keywords, brief_casefold
        )
        reference_adjustment = 0
        if has_reference == "yes" and image_type.reference_policy == "required":
            reference_adjustment += REFERENCE_REQUIRED_BONUS
        elif has_reference == "no" and image_type.id == "personal-ip":
            reference_adjustment -= NO_REFERENCE_PERSONAL_IP_PENALTY
        for profile in _profiles_for(catalog, image_type.id):
            profile_score, profile_matched = _score_phrases(
                profile.title, profile.keywords, brief_casefold
            )
            total_score = type_score + profile_score + reference_adjustment
            matched_terms = list(dict.fromkeys(type_matched + profile_matched))
            sort_key = (
                -total_score,
                image_type.sort_order,
                image_type.id,
                profile.sort_order,
                profile.id,
            )
            candidate = {
                "type": image_type.id,
                "profile": profile.id,
                "score": total_score,
                "category": image_type.category,
                "reference_policy": image_type.reference_policy,
                "matched_terms": matched_terms,
            }
            scored.append((sort_key, candidate))
    scored.sort(key=lambda item: item[0])
    return [candidate for _sort_key, candidate in scored[:ROUTE_CANDIDATE_LIMIT]]


def _emit_route(catalog: Catalog, brief: str, has_reference: str | None, output_format: str) -> None:
    candidates = route_candidates(catalog, brief, has_reference)
    if output_format == "json":
        print(json.dumps(candidates, indent=2, ensure_ascii=False))
        return
    for candidate in candidates:
        matched = "|".join(candidate["matched_terms"])
        print(
            f"{candidate['type']}\t{candidate['profile']}\t{candidate['score']}\t"
            f"{candidate['category']}\t{candidate['reference_policy']}\t{matched}"
        )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        catalog = load_catalog()
        if args.command == "validate":
            print(
                f"Valid image catalog: {len(catalog.types)} types, "
                f"{len(catalog.profiles)} profiles"
            )
            for warning in _profile_keyword_collision_warnings(catalog):
                print(f"warning: {warning}")
            return 0
        if args.command == "list-types":
            if args.grouped:
                _emit_grouped_types(catalog, args.format)
            else:
                _emit_records([record.public_record() for record in catalog.types], args.format)
            return 0
        if args.command == "route":
            _emit_route(catalog, args.brief, args.has_reference, args.format)
            return 0
        image_type = _type_by_id(catalog, args.type)
        if args.command == "list-profiles":
            _emit_records(
                [record.public_record() for record in _profiles_for(catalog, image_type.id)],
                args.format,
            )
            return 0
        if args.command == "resolve":
            result: dict[str, Any] = {
                "type": image_type.public_record(),
                "type_path": str(image_type.path),
                "required_ref_paths": [str(path) for path in image_type.required_ref_paths],
            }
            if args.profile:
                matches = [
                    record
                    for record in _profiles_for(catalog, image_type.id)
                    if record.id == args.profile
                ]
                if not matches:
                    choices = ", ".join(
                        record.id for record in _profiles_for(catalog, image_type.id)
                    )
                    raise CatalogError(
                        f"unknown profile id {args.profile!r} for type {image_type.id!r}; "
                        f"choose one of: {choices}"
                    )
                result["profile"] = matches[0].public_record()
                result["profile_path"] = str(matches[0].path)
            if args.format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"type\t{result['type_path']}")
                for path in result["required_ref_paths"]:
                    print(f"required_ref\t{path}")
                if "profile_path" in result:
                    print(f"profile\t{result['profile_path']}")
            return 0
    except CatalogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
