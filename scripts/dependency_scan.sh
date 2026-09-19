#!/usr/bin/env bash
# Lockfile-only dependency vulnerability scan (control 6.1). Read-only: extracts the manifest and
# lockfile from a git ref into a temp directory and runs the audit there. Nothing is installed.
# Usage: dependency_scan.sh <repo-path> [ref]
# Note: npm audit can take a few minutes on large lockfiles.
set -uo pipefail
REPO="${1:-}"; REF="${2:-HEAD}"
[ -e "$REPO/.git" ] || { echo "usage: $0 <repo-path> [ref]" >&2; exit 2; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
show() { git -C "$REPO" show "$REF:$1" > "$TMP/$1" 2>/dev/null; }

if show package.json && show package-lock.json; then
  echo "ecosystem: npm (package-lock.json)"
  ( cd "$TMP" && npm audit --package-lock-only --json 2>/dev/null ) | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    v=d.get("metadata",{}).get("vulnerabilities",{})
    print("vulnerabilities (includes dev and transitive dependencies; reachability not assessed):")
    for k in ("critical","high","moderate","low","info","total"):
        print("  %-9s %s" % (k, v.get(k,0)))
except Exception as e:
    print("could not parse npm audit output:", e)
'
elif show package.json && show pnpm-lock.yaml; then
  echo "ecosystem: pnpm"; ( cd "$TMP" && pnpm audit --json 2>/dev/null | head -c 2000 )
elif show requirements.txt; then
  echo "ecosystem: python; run: pip-audit -r requirements.txt --dry-run (needs pip-audit)"
else
  echo "No scannable lockfile found at $REF. State this as a structural limitation in the report (dependency scanning could not be run), not as a silent skip."
fi
