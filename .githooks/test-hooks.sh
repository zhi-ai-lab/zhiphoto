#!/bin/sh
# Focused regression tests for the repository-managed Git hooks.

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
pre_push="$repo_root/.githooks/pre-push"
post_merge="$repo_root/.githooks/post-merge"
test_root=$(mktemp -d "${TMPDIR:-/tmp}/release-hooks.XXXXXX")

cleanup() {
  rm -rf -- "$test_root"
}
trap cleanup EXIT HUP INT TERM

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

git init -q --initial-branch=dev "$test_root/repo"
git -C "$test_root/repo" config user.name "Hook Test"
git -C "$test_root/repo" config user.email "hook-test@example.invalid"
git -C "$test_root/repo" commit -q --allow-empty -m initial

printf '%s\n' 'refs/heads/dev 111 refs/heads/dev 000' |
  sh -c 'cd "$1" && "$2" origin https://github.com/example/repository.git' sh "$test_root/repo" "$pre_push"

if printf '%s\n' 'refs/heads/dev 111 refs/heads/main 000' |
  sh -c 'cd "$1" && "$2" origin https://github.com/example/repository.git' sh "$test_root/repo" "$pre_push"; then
  fail "remote main target was accepted"
fi

git -C "$test_root/repo" checkout -q --detach
if printf '%s\n' 'refs/heads/dev 111 refs/heads/dev 000' |
  sh -c 'cd "$1" && "$2" origin https://github.com/example/repository.git' sh "$test_root/repo" "$pre_push"; then
  fail "detached HEAD was accepted"
fi

git -C "$test_root/repo" checkout -q dev
git -C "$test_root/repo" branch main
git -C "$test_root/repo" checkout -q -b topic/merged
git -C "$test_root/repo" commit -q --allow-empty -m merged-topic
git -C "$test_root/repo" checkout -q dev
git -C "$test_root/repo" merge -q --no-ff topic/merged -m merge-topic
(
  cd "$test_root/repo"
  "$post_merge" >/dev/null
)
if git -C "$test_root/repo" show-ref --verify --quiet refs/heads/topic/merged; then
  fail "merged branch was retained"
fi
git -C "$test_root/repo" show-ref --verify --quiet refs/heads/dev
git -C "$test_root/repo" show-ref --verify --quiet refs/heads/main

sh -n "$pre_push" "$post_merge"
echo "Git hook tests passed."
