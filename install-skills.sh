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
#   ./install-skills.sh            # install anything missing, globally
#   ./install-skills.sh --project  # install into ./.agents/skills for this repo
#   ./install-skills.sh --update   # update everything already installed
#   ./install-skills.sh --dry-run  # print the commands, run nothing
#   ./install-skills.sh --yes      # skip the confirmation prompt
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

UPDATE=0
DRY_RUN=0
PROJECT=0
ASSUME_YES=0
for arg in "$@"; do
  case "$arg" in
    --update)  UPDATE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --yes|-y)  ASSUME_YES=1 ;;
    --project) PROJECT=1 ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

command -v npx >/dev/null 2>&1 || {
  echo "error: npx not found. Install Node.js first." >&2; exit 1; }

if [ "$PROJECT" -eq 1 ]; then
  git rev-parse --show-toplevel >/dev/null 2>&1 || {
    echo "error: --project needs a git repo; run from the project root." >&2; exit 1; }
  TARGET="$(git rev-parse --show-toplevel)/.agents/skills"
  SCOPE_FLAG=()
else
  TARGET="${SKILLS_DIR:-$HOME/.agents/skills}"
  SCOPE_FLAG=(-g)
fi

# repo|skill1,skill2,...   (empty skill list = nothing installable upstream)
SOURCES=(
  "pbakaus/impeccable|impeccable"
  "mattpocock/skills|ask-matt,chief-of-staff,claude-handoff,code-review,codebase-design,diagnosing-bugs,domain-modeling,git-guardrails-claude-code,grill-me,grill-with-docs,grilling,handoff,implement,implement-spec,improve-codebase-architecture,loop-me,migrate-to-shoehorn,pr,research,retro,scaffold-exercises,setup-matt-pocock-skills,setup-pre-commit,setup-ts-deep-modules,tdd,teach,to-questionnaire,to-spec,to-tickets,triage,wait-what,wayfinder,wizard,writing-beats,writing-for-agents,writing-fragments,writing-shape"
  "emilkowalski/skills|emil-design-eng,animate,animate-expo,animation-performance,review-animations,improve-animations,find-animation-opportunities,animation-vocabulary,apple-design,write-swift,pick-ui-library,prototype,mobile-native,break-ui,ask-sonner"
  "alejandrobailo/no-use-effect|no-use-effect"
  "obra/superpowers|using-git-worktrees,using-superpowers"
  "vercel-labs/agent-browser|agent-browser"
  "vercel-labs/skills|find-skills"
  "jakubkrehel/make-interfaces-feel-better|make-interfaces-feel-better"
  "browser-use/browser-use|browser-use"
  "blader/humanizer|humanizer"
  "makenotion/skills|notion-cli"
  "intellectronica/agent-skills|raindrop-api"
  "PleasePrompto/notebooklm-skill|notebooklm"
  "omacom/omarchy|omarchy,diagnose-crash,omarchy-app"
  "ayghri/i-have-adhd|i-have-adhd"
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

# Credit the author of a source, read from skills.json.
#
# Printing only the repository name attributes the work to nobody, and a user
# who cannot see the licence at install time cannot know what they just agreed
# to. ATTRIBUTION.md is generated from this same record, so the credit here and
# the credits file cannot disagree.
credit() {
  python3 - "$1" <<'PY' 2>/dev/null || true
import json, sys
repo = sys.argv[1]
try:
    data = json.load(open("skills.json"))
except Exception:
    sys.exit(0)
for source in data.get("sources", []):
    if source.get("repo") == repo:
        lic = (source.get("license") or "").strip()
        if lic.lower() in ("", "none", "unknown"):
            lic = "no licence — all rights reserved"
        print(f"  by {source.get('author', 'unknown')} · {lic}")
        break
PY
}

# Gate every install behind an explicit yes.
#
# A skill is instructions the agent will follow, fetched from a stranger's
# repository and then loaded by every harness on the machine. That is not
# something to do on the user's behalf without showing them the list first.
# --dry-run and --yes are the two ways past this prompt; a non-interactive
# shell must pass --yes rather than block forever.
confirm() {
  [ "$DRY_RUN" -eq 1 ] && return 0
  [ "$ASSUME_YES" -eq 1 ] && return 0
  if [ ! -t 0 ]; then
    echo "error: no terminal to confirm on. Re-run with --yes, or --dry-run to preview." >&2
    exit 1
  fi
  printf '\nProceed? [y/N] '
  # EOF is a no, not a crash. Under `set -e` a bare `read` that hits EOF
  # aborts the script, so the user gets a stack of nothing instead of the
  # one line that says why nothing was installed.
  if ! read -r reply; then
    echo
    echo "Nothing installed (no answer read)."
    exit 0
  fi
  case "$reply" in
    y|Y|yes|YES) return 0 ;;
  esac
  echo "Nothing installed."
  exit 0
}

# One line per source: repo, author, licence, and how many skills it installs.
preview() {
  local total=0
  for entry in "${SOURCES[@]}"; do
    local repo="${entry%%|*}" skills="${entry#*|}" n=0
    if [ -n "$skills" ]; then
      IFS=',' read -r -a _names <<< "$skills"
      n=${#_names[@]}
    fi
    total=$((total + n))
    echo "• $repo"
    credit "$repo"
  done
  echo
  echo "$total skill(s) from ${#SOURCES[@]} source(s) → $TARGET"
  echo "Authors and licences for all of them: ATTRIBUTION.md"
}

if [ "$UPDATE" -eq 1 ]; then
  echo "Updating installed skills from their upstream sources…"
  echo "(every source in ~/.agents/.skill-lock.json is fetched and rewritten)"
  confirm
  run npx --yes skills@latest update -g -y || true

  echo
  echo "• kerpopule/hermes-jev-skills (via its own installer)"
  credit "kerpopule/hermes-jev-skills"
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
echo
preview
confirm
echo

for entry in "${SOURCES[@]}"; do
  repo="${entry%%|*}"
  skills="${entry#*|}"

  if [ -z "$skills" ]; then
    echo "• $repo — nothing installable upstream, skipping"
    credit "$repo"
    continue
  fi

  echo "• $repo"
  credit "$repo"
  args=(npx --yes skills@latest add "$repo" ${SCOPE_FLAG[@]+"${SCOPE_FLAG[@]}"} -y)
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
credit "kerpopule/hermes-jev-skills"
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
echo "Authors and licences for everything installed: ATTRIBUTION.md"
