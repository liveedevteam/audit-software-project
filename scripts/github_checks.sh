#!/usr/bin/env bash
# Read-only GitHub checks (controls 3.1 to 3.3, 6.1). Uses only GET requests via the gh CLI.
# Usage: github_checks.sh <owner/repo> [branch]
# A 403/404 means "not enabled or not visible": report Not Verified, not absent.
set -uo pipefail
REPO="${1:-}"; BRANCH="${2:-}"
[ -n "$REPO" ] || { echo "usage: $0 <owner/repo> [branch]" >&2; exit 2; }
command -v gh >/dev/null || { echo "gh CLI not found" >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated" >&2; exit 2; }
api() { gh api -X GET "$@"; }

[ -n "$BRANCH" ] || BRANCH="$(api "repos/$REPO" --jq .default_branch)"
echo "repo: $REPO   branch: $BRANCH   visibility: $(api "repos/$REPO" --jq .visibility)"

echo "== branch protection (3.1, 3.3)"
if out=$(api "repos/$REPO/branches/$BRANCH/protection" 2>&1); then
  echo "$out" | python3 -c '
import json,sys
p=json.load(sys.stdin)
rv=p.get("required_pull_request_reviews")
sc=p.get("required_status_checks") or {}
print("  required PR reviews :", "yes (%s approvals)" % rv.get("required_approving_review_count") if rv else "NO")
print("  required checks     :", len(sc.get("contexts",[])) + len(sc.get("checks",[])), "configured")
print("  enforce for admins  :", (p.get("enforce_admins") or {}).get("enabled"))
'
else
  echo "  not protected or not visible: $(echo "$out" | head -c 120)"
fi

echo "== security features (6.1)"
api "repos/$REPO" --jq '.security_and_analysis | to_entries[] | "  \(.key): \(.value.status)"' 2>/dev/null || echo "  not visible"
if gh api -X GET "repos/$REPO/vulnerability-alerts" -i 2>/dev/null | head -1 | grep -q "204"; then echo "  dependabot alerts: enabled"; else echo "  dependabot alerts: not enabled or not visible"; fi

echo "== review sample of recent merged PRs (3.2)"
gh pr list -R "$REPO" --state merged --limit 20 --json number,reviews --jq '[.[]|(.reviews|length)>0] | "  reviewed: \(map(select(.))|length) of \(length)"' 2>/dev/null || echo "  not available"
