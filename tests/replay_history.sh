#!/usr/bin/env bash
# Replay the canon check against real history: for each commit, recreate the
# moment just before it was committed and report whether the hook would block.
#
# usage: replay_history.sh <repo> [--canon <globs-file>] <rev-list args...>
# e.g.   replay_history.sh ~/src/engine --canon canon.txt origin/main..HEAD
#        replay_history.sh ~/src/engine --canon canon.txt -n 80 main -- AGENTS.md docs
set -euo pipefail

repo=$(cd "$1" && pwd); shift
canon=""
if [ "${1:-}" = "--canon" ]; then canon=$(cd "$(dirname "$2")" && pwd)/$(basename "$2"); shift 2; fi
revs=("$@")
check=$(cd "$(dirname "$0")/../plugin/scripts" && pwd)/canon_check.py
work=$(mktemp -d)
trap 'git -C "$repo" worktree remove --force "$work" >/dev/null 2>&1 || true' EXIT
git -C "$repo" worktree add -q --detach "$work" HEAD

checked=0; blocked=0
for c in $(git -C "$repo" rev-list --no-merges --reverse "${revs[@]}"); do
  git -C "$work" rev-parse -q --verify "$c~1" >/dev/null || continue
  git -C "$work" checkout -q -f --detach "$c~1"
  git -C "$work" clean -qfd
  git -C "$repo" diff --name-only "$c~1" "$c" | while read -r f; do
    git -C "$work" checkout -q "$c" -- "$f" 2>/dev/null || rm -f "$work/$f"
  done
  if [ -n "$canon" ]; then mkdir -p "$work/.nomad-method"; cp "$canon" "$work/.nomad-method/canon"; fi
  checked=$((checked + 1))
  if out=$(printf '{"cwd":"%s","tool_input":{"command":"git commit -m x"}}' "$work" | python3 "$check" 2>&1); then
    :
  else
    blocked=$((blocked + 1))
    echo "BLOCK $(git -C "$repo" log --oneline -1 "$c" | cut -c1-72)"
    echo "$out" | grep -A1 '^- ' | sed 's/^/      /'
  fi
  git -C "$work" reset -q --hard
done
echo "checked=$checked blocked=$blocked"
