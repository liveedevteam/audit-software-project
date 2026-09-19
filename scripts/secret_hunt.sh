#!/usr/bin/env bash
# Standard secret hunt (control 3.4). Prints LOCATIONS AND TYPES ONLY, never the matched text.
# Usage: secret_hunt.sh <repo-path> [ref]     (ref defaults to HEAD; use origin/<branch> for the remote state)
set -uo pipefail
REPO="${1:-}"; REF="${2:-HEAD}"
[ -d "$REPO/.git" ] || [ -f "$REPO/.git" ] || { echo "usage: $0 <repo-path> [ref]" >&2; exit 2; }
G=(git -C "$REPO")

echo "== tracked files named like env/credential/secret/key material (names only)"
"${G[@]}" ls-tree -r --name-only "$REF" | grep -iE '(^|/)\.env($|\.)|credential|secret|\.pem$|\.key$|id_rsa|\.p12$|\.pfx$' | grep -viE '\.example$|\.sample$|\.template$' || echo "(none)"

echo "== secret-shaped strings (path:line and type; values are not printed)"
scan() {  # scan <type> <regex>
  local type="$1" rx="$2" hits
  hits=$("${G[@]}" grep -nIE "$rx" "$REF" -- . ':!*lock*' ':!*.lock' ':!package-lock.json' ':!pnpm-lock.yaml' 2>/dev/null | awk -F: '{print $2":"$3}')
  [ -n "$hits" ] && echo "$hits" | sed "s/\$/  [$type]/"
}
scan "AWS access key id"        'AKIA[0-9A-Z]{16}'
scan "Stripe-style secret key"  '(sk|rk)_live_[A-Za-z0-9]{10,}'
scan "private key block"        '-----BEGIN (RSA|EC|OPENSSH|PGP|DSA)? ?PRIVATE KEY-----'
scan "credential in URL"        '[a-z]+://[^ /:"'"'"']+:[^ @"'"'"']{4,}@'
scan "JWT"                      'eyJ[A-Za-z0-9_-]{20,}\.eyJ'
scan "GitHub token"             '(ghp|gho|ghs)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'
scan "Slack token"              'xox[bpars]-[A-Za-z0-9-]{10,}'
scan "Google API key"           'AIza[0-9A-Za-z_-]{35}'
echo "== history: deleted env files (names only)"
"${G[@]}" log --all --diff-filter=D --name-only --format= -- '*.env' '*.env.*' 2>/dev/null | sort -u | grep -viE '\.example$|\.sample$' || echo "(none)"
echo
echo "Triage each hit by reading the location yourself: placeholders, test fixtures, publishable keys and documented example values (for example the AWS docs example key ending in EXAMPLE) are not live secrets; record them as Low or drop them, and say why."
echo "A live-looking secret is an immediate blocker; record its location and type only."
