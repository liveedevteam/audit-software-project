# Audit controls

~35 controls across 10 domains. Each control lists the evidence to look for,
what Green requires, and what makes it Red. Amber is the space between —
partial, inconsistent, or moderate-risk — call it out explicitly only where
the boundary isn't obvious. Not Verified when evidence is inaccessible; state
why. Not Applicable when the control doesn't fit the project; state why.

Calibrate every judgment to the intake risk profile (internal tool vs.
customer-facing, personal data or not, deployment model).

---

## 1. Ownership and accountability

**1.1 Named technical owner**
Evidence: CODEOWNERS file, README "maintainers" section, recent commit
authorship concentration.
Green: a clear owner or on-call rotation is identifiable.
Red: no way to identify who is responsible for the project at all, and it's
in active production use.

**1.2 Decision record for significant changes**
Evidence: ADR directory, design-doc links in PR descriptions, architecture docs.
Green: significant technical decisions have a written rationale somewhere.
Red: no record of any decision anywhere, on a project old/complex enough that
this creates real risk (e.g., undocumented reasons for a nonstandard
architecture choice).

**1.3 Knowledge concentration (bus factor)**
Evidence: `git shortlog -sn --since="1 year ago"` overall, then re-run scoped
to the highest-risk paths identified in step 2 (e.g. `-- 'src/payments/**'
'src/auth/**'`) to see whether concentration is worse in critical code than
project-wide.
Green: multi-contributor project where critical-path code has been touched
by more than one person in the last year, or the project is a knowingly
solo/hobby effort (state that explicitly — Not Applicable, not Red).
Amber: overall contribution is spread out, but a specific critical-path area
(auth, payments, infra) has been touched by only one person in the last year.
Red: a multi-contributor, actively-used production project where nearly all
commits across the whole history are from one author who is no longer
active (check `git log -1 --format=%ad -- <author's files>` for staleness),
with no CODEOWNERS/rotation from 1.1 to mitigate it.

---

## 2. Requirements and acceptance criteria

**2.1 Traceable requirements**
Evidence: issue tracker links in commits/PRs, linked tickets, spec docs.
Green: most non-trivial changes reference a requirement or ticket.
Red: no traceability at all and the project has multiple contributors.

**2.2 Acceptance criteria on delivered work**
Evidence: PR template, PR descriptions, issue templates.
Green: PRs/issues typically state what "done" means.
Not Applicable: solo hobby project with no external requirements process.

---

## 3. Repository and source-control safeguards

**3.1 Branch protection on default branch** *(GitHub check)*
Evidence: `gh api repos/{owner}/{repo}/branches/{default}/protection` (read-only).
Green: protection enabled, requires PR + at least one review before merge.
Red: default branch accepts direct pushes with no review requirement.
Not Verified: `gh` not authorized/declined at intake.

**3.2 PRs actually get reviewed** *(GitHub check)*
Evidence: `gh pr list --state merged --json reviews` sample of recent merges.
Green: majority of sampled merged PRs show at least one review.
Red: sampled PRs show no reviews despite protection nominally requiring them,
or protection is off and it's evident PRs are self-merged.

**3.3 CI required to pass before merge** *(GitHub check)*
Evidence: branch protection required status checks, `.github/workflows`.
Green: CI is required and covers build/test at minimum.
Red: CI exists but is not required, or doesn't exist at all.

*Additional cheap GitHub reads while authenticated (report under 3.x/6.1):*
`gh repo view --json visibility` (public repo + committed secret = much
larger blast radius), and `gh api repos/{owner}/{repo}/vulnerability-alerts`
plus `.../secret-scanning/alerts` (404/403 = not enabled or not visible —
report as Not Verified, not absent).

**3.4 No secrets committed to history**
Evidence: run the standard hunt below — the same one every time, so runs
are comparable. Cite location/type only, never the value.
Green: no live-looking secrets found in tree or reachable history.
Red: a live-looking secret is found — **always Red, always immediate
blocker**, regardless of risk profile.

*Standard secret/PII hunt (minimum required, add more if the stack suggests it):*
1. `git ls-files | grep -iE '\.env|credential|secret'` — any tracked env or
   credential-named file. A tracked `.env` (not `.example`) is a finding in
   itself even before reading it.
2. Grep tracked files (excluding lockfiles) for the pattern set:
   `AKIA[0-9A-Z]{16}` (AWS), `sk_live_` / `rk_live_` (Stripe secret),
   `-----BEGIN (RSA|EC|OPENSSH|PGP|PRIVATE) KEY-----`,
   `[a-z]+://[^ /:]+:[^ @]{4,}@` (credential-bearing URLs),
   `eyJ[A-Za-z0-9_-]{20,}\.eyJ` (JWTs), `ghp_|gho_|github_pat_` (GitHub),
   `xox[bpars]-` (Slack), `AIza[0-9A-Za-z_-]{35}` (Google API).
3. History of deleted env files: `git log --all --diff-filter=AD --format="%h" -- '*.env*'`
   then a bounded `git log -p -- '*.env*'` scan — a secret deleted from HEAD
   is still leaked.
4. Distinguish live-looking from placeholder: `[PASSWORD]`, `your_*_here`,
   `example`, obviously-dummy CI values are Green context, not findings.
   Publishable/anon keys designed for client exposure (Stripe `pk_`,
   Supabase anon) are not secrets — say so to preempt false alarms.
5. PII sweep (feeds control 6.3): grep migrations, seeds, and fixtures for
   real-looking emails (`@gmail|@yahoo|@hotmail|@outlook` plus any domain
   matching the client's), phone-number shapes, and person-named variables;
   real-looking personal data is treated exactly like a secret.

**3.5 .gitignore covers secrets/build artifacts**
Evidence: `.gitignore` content vs. tracked files.
Green: `.env*`, credentials, build output are ignored and not tracked.
Amber: gitignore exists but incomplete (e.g., misses `.env.local`).

**3.6 Commit message hygiene**
Evidence: sample the most recent 50 commit messages
(`git log -50 --format=%s`).
Green: messages generally describe intent (what/why), even briefly.
Amber: mixed — a meaningful fraction are non-descriptive (`fix`, `wip`,
`asdf`, `.`, `updates`) but not the majority.
Red: majority of sampled messages are non-descriptive, on a
multi-contributor project (single-author scratch/experimental repos: Not
Applicable — state so explicitly).

**3.7 Repository bloat and tracked build artifacts**
Evidence: `git rev-list --objects --all` piped through `git cat-file
--batch-check` sorted by size (or `git count-objects -v` as a cheap proxy)
for large blobs in history; cross-check large/binary tracked files against
3.5's `.gitignore` findings.
Green: no unexpectedly large blobs in history; build output/dependency
directories are not tracked.
Amber: build artifacts or large binaries (>~5MB) are tracked in the current
tree but don't dominate the repo.
Red: build output, dependency directories (e.g. `node_modules`,
`vendor`), or large binaries are tracked in history at a scale that would
materially slow clones or indicates `.gitignore` was added after the fact
without cleanup.

---

## 4. Code quality and maintainability

**4.1 Linting/formatting enforced**
Evidence: linter config, CI step running it, pre-commit hooks.
Green: a linter runs in CI and blocks merge on failure.
Red: no linting at all in a multi-contributor codebase.

**4.2 Dependency currency**
Evidence: lockfile dates, `npm outdated`/equivalent, known-EOL runtime versions.
Green: dependencies and runtime are within roughly a year of current, or
there's an active update process (Dependabot/Renovate).
Red: critical dependencies or runtime are multiple major versions behind
with known deprecation/EOL, and no update process exists.

**4.3 No obvious dead/duplicated critical logic**
Evidence: spot-check for copy-pasted business logic, commented-out code blocks.
Amber/Red judgment only — this is the softest control; keep findings narrow
and cite specific files, don't generalize.

**4.4 License declared and dependency licenses compatible**
Evidence: LICENSE/LICENSE.md file at repo root; `package.json` `license`
field; a lockfile-metadata license listing where cheaply available (e.g.
`npx license-checker --summary`, `pip-licenses`) — skip the scan itself if
it would require installing tooling, and say so.
Green: a license is declared for a commercial/shared/customer-facing
project, and no copyleft (GPL/AGPL) dependency is bundled into a
closed-source product in a way that looks like a conflict.
Not Applicable: private internal tool never distributed outside the org.
Red: code is published, sold, or distributed with no license at all, or an
AGPL/GPL dependency is bundled into a proprietary distributed product.

**4.5 Configuration hardcoded in source**
Evidence: grep source (excluding tests/fixtures) for `http://localhost`,
literal IP addresses, hardcoded ports, and environment-branching logic
scattered outside a config module (`if.*NODE_ENV.*==.*['"]production`
repeated across many files rather than centralized).
Green: environment-specific values are read from config/env, not
literals in business logic.
Amber: a handful of hardcoded values exist but are low-risk (e.g. a default
dev port) and don't affect production behavior.
Red: production-relevant values (API endpoints, credentials-adjacent
config) are hardcoded and would require a code change to alter per
environment.

**4.6 Unresolved TODO/FIXME debt in critical paths**
Evidence: `grep -rn 'TODO\|FIXME\|HACK' --include=<source ext>` scoped to
the highest-risk feature areas (auth, payments, data mutation) identified
in step 2.
Amber-tier only — this is a soft signal, not a failure condition. Amber:
critical-path files contain TODO/FIXME/HACK markers describing known-unsafe
or known-incomplete behavior (e.g. "TODO: validate this before prod").
Green: none found, or markers found are cosmetic/non-critical.

**4.7 Type safety on critical paths**
Evidence: presence and strictness of static/gradual typing (TypeScript
`strict` in `tsconfig.json`, mypy config, Sorbet, etc.) applied to
auth/payments/data-mutation code, versus unchecked dynamic code there.
Green: critical-path code is statically typed, or the language is
inherently statically typed.
Amber: typing tooling is present but not enforced in strict mode, or only
partially applied to critical paths.
Red: critical-path code is written in a dynamically-typed language with no
type-checking tooling at all, on a multi-contributor production project.

---

## 5. Automated testing and critical behavior coverage

**5.1 Tests exist and run**
Evidence: test directory/framework, `package.json`/`Makefile` test script,
CI step executing tests.
Green: tests exist and are executed in CI.
Red: no automated tests at all.

**5.2 Critical business paths are covered**
Evidence: test file names/contents mapped against apparent core features
(auth, payments, data mutation).
Green: the riskiest user flows have some automated coverage.
Red: critical flows (money, auth, data loss) have zero test coverage.
Not Verified: can't determine what's "critical" without domain context —
ask at intake or list as a question.

**5.3 Tests aren't silently skipped/broken**
Evidence: `.skip`/`xit`/`@Disabled` markers, CI status history if accessible.
Amber: a meaningful number of tests are skipped without a tracked reason.

**5.4 Integration/e2e coverage on critical flows**
Evidence: test files exercising a full flow (API call through to
persistence, or a browser/e2e runner) versus unit tests that only cover
isolated functions in isolation, for the critical flows identified in
step 2. Complements 5.2 — a critical flow can be Green on 5.2 (some
coverage exists) while still Amber/Red here if that coverage is unit-only.
Green: at least one critical flow has integration/e2e-level coverage.
Amber: critical flows have unit coverage only, no integration/e2e layer
exists at all.
Not Verified: can't determine test boundary type from file names/content
alone.

---

## 6. Security, secrets, dependencies, and production access

**6.1 Dependency vulnerability scanning**
Evidence: Dependabot/Snyk config, plus a lockfile-only scan run as part of
this audit by default (`npm audit --package-lock-only` / `pnpm audit` /
ecosystem equivalent — read-only, no installs).
Green: automated scanning configured, or the audit-run scan finds no
high/critical issues.
Red: no scanning and the audit-run scan surfaces high/critical known
vulnerabilities.
Structural limitation to state explicitly when it applies: URL-import
ecosystems with no lockfile (e.g., Deno edge functions importing from
esm.sh/deno.land) cannot be scanned this way — those dependencies are
invisible to SCA tooling and that fact is itself a finding to report,
not a silent skip.

**6.2 Production access control**
Evidence: docs describing who can deploy/access prod, env var handling,
`.env.example` vs real secrets separation.
Green: clear separation between example/config templates and real secrets;
access process is documented.
Not Verified: no way to see prod access from repo alone — this is expected;
becomes an intake question.

**6.3 Personal/sensitive data handling**
Evidence: schema/model files, seed/fixture data, field names suggesting PII.
Green: no real-looking personal data committed; sensitive fields are
clearly synthetic in fixtures.
Red: real-looking personal data (names, emails, real-seeming identifiers)
found committed — treated like a secret: cite location/type only, always
an immediate blocker regardless of risk profile.

---

## 7. CI/CD, deployment repeatability, and rollback

**7.1 Deployment is defined as code/config, not manual steps**
Evidence: CI/CD pipeline files, IaC, deploy scripts vs. a README saying
"SSH in and run X."
Green: deployment is scripted/automated and reproducible.
Red: deployment depends on undocumented manual steps only one person knows.

**7.2 Rollback path exists**
Evidence: rollback documented in pipeline, versioned releases/tags,
database migration down-scripts.
Not Verified: usually can't confirm rollback actually works from repo alone
— note as a question rather than a failure.
Red: evidence affirmatively shows no rollback is possible (e.g.,
irreversible migrations with no backup strategy mentioned anywhere).

---

## 8. Architecture, trust boundaries, APIs, and data

**8.1 Trust boundaries are identifiable**
Evidence: auth middleware, input validation at API boundaries.
Green: external inputs are validated before use; auth is enforced on
sensitive endpoints.
Red: sensitive endpoints (data mutation, admin actions) found with no
visible auth check.

**8.2 Database migrations are safe and reviewed**
Evidence: migration directory, whether migrations go through the same PR/review process.
Green: migrations are version-controlled and reviewed like other code.
Amber: migrations exist but bypass normal review.

**8.3 Input validation at API boundaries**
Evidence: grep route/handler files for a validation layer (zod, joi,
pydantic, class-validator, JSON Schema, etc.) versus raw `req.body`/
`request.json()`/equivalent consumed directly in sensitive handlers
(payment, auth, admin, data-mutation endpoints identified in step 2).
Green: external input to sensitive endpoints passes through a validation
layer before use.
Red: a sensitive mutation (money, auth, admin, PII) consumes raw unvalidated
input directly — this is a narrower, code-verifiable companion to 8.1's
broader "is auth enforced" check, not a replacement for it.

**8.4 Injection surface**
Evidence: grep tracked source (excluding tests/vendored code) for the
pattern set: string-built SQL (`` `SELECT ` `` / `f"SELECT` / `"SELECT" +`
concatenation instead of parameterized queries), `eval(`, `exec(` on
non-literal input, `child_process.exec`/`os.system`/`subprocess.shell=True`
with interpolated variables, `dangerouslySetInnerHTML`/`innerHTML =` fed
from user input without sanitization.
Green: no such pattern found reachable from user input, or found instances
use parameterized/escaped equivalents (ORMs, prepared statements,
`textContent`).
Red: a user-reachable code path feeds unsanitized input into one of these
sinks.

**8.5 Error handling discipline on critical paths**
Evidence: grep critical-path files (auth, payments, data mutation) for
empty or logging-only catch blocks (`catch {}`, `except: pass`,
`except Exception: continue`), and unhandled promise rejections.
Green: errors on critical paths are surfaced (thrown, logged with context,
or returned as a response) rather than silently discarded.
Amber: swallowed errors exist but are confined to non-critical paths.
Red: a critical path (payment processing, auth check, data write) silently
swallows errors such that failure would be invisible to both user and
operator.

---

## 9. Operations, monitoring, alerts, backups, and recovery

**9.1 Monitoring/observability present**
Evidence: logging config, APM/error-tracking SDK (Sentry, Datadog, etc.) in dependencies.
Green: error tracking and basic monitoring are wired into the app.
Not Verified: dashboards/alerts live outside the repo — ask at intake.
Red: production-facing app with zero error tracking or logging strategy visible anywhere.

**9.2 Backups exist for stateful data**
Evidence: almost never visible from a repo alone.
Not Verified by default — this is expected, not a failure. Ask at intake.
Red only if there's affirmative repo evidence backups were disabled or removed.

**9.3 Alerting configured, not just monitoring installed**
Evidence: alert-rule config in repo (Sentry alert rules, Datadog
monitors-as-code, PagerDuty/Opsgenie integration config) versus only an
SDK/dependency for error tracking with no visible rule configuration.
Depends on 9.1: only evaluated when 9.1 is Green (monitoring exists) —
if 9.1 is Red, 9.3 is Not Applicable, since there's nothing to alert on.
Green: alerting rules are defined in-repo, or the project owner confirms
at intake that alerts are configured in the vendor dashboard.
Not Verified: alert configuration typically lives outside the repo and
the owner wasn't asked or didn't answer — default when 9.1 is Green and
no rule config is visible in-repo.
Red: the project owner affirmatively confirms at intake that monitoring
is installed but no alerts are configured (error tracking exists but no
one gets paged) — a Red here requires that confirmation, not repo
absence alone.

---

## 10. Documentation and operational knowledge

**10.1 README covers setup and purpose**
Evidence: README content.
Green: a newcomer could get the project running from the README alone.
Red: no README, or one that's inaccurate/severely outdated (e.g.,
references a deleted stack).

**10.2 Runbook/operational docs for production issues**
Evidence: docs describing what to do during an incident.
Not Verified: expected for many projects — ask at intake if project is
production-facing.
Amber: exists but clearly stale (references old infra/tools).

---

## 11. Performance and scalability

All controls in this domain are grep-tier evidence and do not expand the
audit's deep-read budget (see SKILL.md step 3).

**11.1 Unbounded queries**
Evidence: grep hot-path data-access code (list/index endpoints, feeds,
search) for queries with no pagination or `LIMIT`/`take`/`first` bound —
`findAll`-style calls feeding a user-facing response.
Green: user-facing list endpoints are paginated or otherwise bounded.
Red: a user-facing endpoint returns an unbounded result set from a table
that can grow without limit in production use.

**11.2 N+1 query patterns**
Evidence: grep critical-path code for a database call issued inside a
loop over a previously-fetched collection (classic N+1 shape), versus use
of a join/batch-load/eager-loading mechanism.
Amber-tier only — this is a performance smell, not a binary failure.
Amber: an N+1 shape is found in a critical, user-facing path.
Green: no such pattern found, or found instances are already batched.

**11.3 Resource limits on external-facing endpoints**
Evidence: grep server/framework config and route handlers for request
timeouts, body-size limits, and rate limiting versus endpoints with none
configured anywhere (global or per-route).
Green: timeouts and body-size limits are set globally or per-endpoint.
Red: a user-facing, unauthenticated endpoint has no timeout, no body-size
cap, and no rate limit — this doubles as a security finding (DoS vector)
and should be prioritized as such under the existing risk-priority order.

**11.4 Caching on read-heavy paths**
Amber-tier only, never Red — repo evidence alone cannot establish that a
path actually needs caching; treat like 4.3/4.6.
Evidence: presence of any caching layer (Redis/Memcached client, CDN or
`Cache-Control` headers, framework-level memoization) cross-checked
against endpoints performing expensive aggregate/computed reads.
Amber: an expensive computed-read endpoint exists with no caching
anywhere, AND there is repo evidence of an acknowledged performance
concern (a slow-query TODO, a timeout value raised specifically for that
endpoint).
Green: caching is present where expensive reads exist, or no evidence of
an expensive read path was found.

---

## 12. API contract and versioning discipline

Not Applicable in full when nothing external consumes the project's API
(internal-only tool, no published SDK or partner integration) — confirm
at intake (see SKILL.md step 1).

**12.1 API surface is documented**
Evidence: OpenAPI/Swagger spec, GraphQL schema file, or a generated/typed
client package, versus routes discoverable only by reading handler code.
Green: the external API surface has a machine-readable or published spec.
Red: an externally-consumed API has no documentation of its surface
anywhere, requiring reverse-engineering from source to integrate.

**12.2 Breaking changes are versioned or gated**
Evidence: versioned route prefixes (`/v1/`, `/v2/`), API changelog,
deprecation-header usage, or a documented deprecation policy.
Green: breaking changes go through a version bump or deprecation window.
Red: evidence of a breaking change shipped to an existing endpoint with no
version change and no deprecation notice (e.g., a field removed or
renamed in place on a documented public endpoint).

**12.3 Backward-compatibility policy for public/partner APIs**
Evidence: written compatibility policy (README, docs site, API changelog
preamble) stating what consumers can rely on.
Not Verified: no such policy is visible but the API is young/small — note
as a question rather than a failure.
Green: a compatibility policy exists and is discoverable by API consumers.

---

## 13. (intentionally unused)

Reserved — accessibility and internationalization were considered for
this slot and deliberately excluded: static analysis cannot verify a11y
compliance with enough confidence for an audit deliverable, and a false
verdict costs more than an absent one. Reports state this exclusion
explicitly in the inspection-boundary section (see SKILL.md). The number
is left unused rather than reassigned, so a future a11y/i18n domain (if
ever added, backed by real browser-based tooling) can occupy it without
renumbering anything else.

---

## 14. Data lifecycle and retention

**14.1 Retention/deletion policy**
Evidence: almost never visible from a repo alone — same shape as 9.2.
Not Verified by default; becomes an intake/report question when the
project handles PII (per control 6.3).
Red only on affirmative repo evidence of a violation (e.g., a comment or
doc stating user data is never deleted, on a project serving users under
a data-protection regime such as GDPR/CCPA).

**14.2 Deletion actually deletes**
Evidence: locate the account/data-deletion endpoint or flow and read it
(this may claim one deep-read slot from the audit's budget when the
project handles PII — see SKILL.md step 3). Check whether "deleted" data
remains queryable/served afterward, and whether soft-deleted PII has any
purge path.
Green: deletion is a hard delete, or a soft delete with a working purge
job/process.
Amber: soft-delete exists with no purge path, but the product makes no
explicit deletion promise to users.
Red: "deleted" user PII remains queryable or is still served through the
application after a user-facing deletion action, while the product
promises deletion — this is a privacy/sensitive-data exposure and is
prioritized as rung 1 under the existing risk-priority order (same tier
as 6.3).
Not Applicable: the project stores no meaningful PII.
