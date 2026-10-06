#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# install-skills.sh — (re)install the third-party skills listed in
# skills.json into ~/.agents/skills.
#
# Those skills are deliberately not stored in this repository: they
# belong to their original authors. This script fetches them from their
# upstream sources instead, so they stay current and correctly licensed.
#
# Usage:
#   ./install-skills.sh            # install anything missing
#   ./install-skills.sh --update   # update everything already installed
#   ./install-skills.sh --dry-run  # print the commands, run nothing
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

UPDATE=0
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --update)  UPDATE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

command -v npx >/dev/null 2>&1 || {
  echo "error: npx not found. Install Node.js first." >&2; exit 1; }

TARGET="${SKILLS_DIR:-$HOME/.agents/skills}"

# repo|skill1,skill2,...   (empty skill list = nothing installable upstream)
SOURCES=(
  "pbakaus/impeccable|impeccable"
  "mattpocock/skills|grill-me,grill-with-docs,handoff,improve-codebase-architecture,prototype,setup-matt-pocock-skills,tdd,triage,codebase-design,domain-modeling,grilling"
  "obra/superpowers|using-git-worktrees,using-superpowers"
  "vercel-labs/agent-browser|agent-browser"
  "vercel-labs/skills|find-skills"
  "jakubkrehel/make-interfaces-feel-better|make-interfaces-feel-better"
  "browser-use/browser-use|browser-use"
  "blader/humanizer|humanizer"
  "makenotion/skills|notion-cli"
  "intellectronica/agent-skills|raindrop-api"
  "PleasePrompto/notebooklm-skill|notebooklm"
)

# The Jev skills ship their own installer and are handled separately below,
# because `npx skills add` skips the whole repo over one malformed file.
JEV_REPO="https://github.com/kerpopule/hermes-jev-skills"

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '  %s\n' "$*"
  else
    "$@"
  fi
}

if [ "$UPDATE" -eq 1 ]; then
  echo "Updating installed skills from their upstream sources…"
  run npx --yes skills@latest update -g -y || true

  echo
  echo "• kerpopule/hermes-jev-skills (via its own installer)"
  run bash -c '
    set -e
    src="${XDG_CACHE_HOME:-$HOME/.cache}/hermes-jev-skills"
    [ -d "$src/.git" ] || git clone --depth 1 "$1" "$src"
    git -C "$src" pull --ff-only
    python3 "$src/install.py"
  ' _ "$JEV_REPO" || echo "  ! jev installer reported an error (see above)"
  exit 0
fi

echo "Installing third-party skills into: $TARGET"
echo "(skills.json in this repository describes each source and its licence)"
echo

for entry in "${SOURCES[@]}"; do
  repo="${entry%%|*}"
  skills="${entry#*|}"

  if [ -z "$skills" ]; then
    echo "• $repo — nothing installable upstream, skipping"
    continue
  fi

  echo "• $repo"
  args=(npx --yes skills@latest add "$repo" -g -y)
  IFS=',' read -r -a names <<< "$skills"
  for name in "${names[@]}"; do
    args+=(-s "$name")
  done

  run "${args[@]}" || echo "  ! $repo reported an error (see above)"
  echo
done

# Jev skills: use their own installer rather than `npx skills add`, which skips
# the repository entirely because one of its files has malformed frontmatter.
echo "• kerpopule/hermes-jev-skills (via its own installer)"
run bash -c '
  set -e
  src="${XDG_CACHE_HOME:-$HOME/.cache}/hermes-jev-skills"
  [ -d "$src/.git" ] || git clone --depth 1 "$1" "$src"
  git -C "$src" pull --ff-only
  python3 "$src/install.py"
' _ "$JEV_REPO" || echo "  ! jev installer reported an error (see above)"
echo

echo "Done. Skills that upstream has renamed or withdrawn are listed under"
echo "\"notAvailableUpstream\" in skills.json."
