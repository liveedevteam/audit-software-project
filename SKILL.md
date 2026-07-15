---
name: audit-software-project
description: Perform a minimum evidence-based engineering audit of a local software repository. Use when asked to audit a codebase, assess production readiness, check engineering controls, or produce a 30-day improvement plan for a project. Read-only unless the user explicitly authorizes remediation.
---

# audit-software-project

Inspect a local repository, collect verifiable evidence across 13 engineering
domains (~47 controls, each Green/Amber/Red/Not Verified/Not Applicable), then
report findings **organized by product feature/area** — not by abstract domain
number — so a team can see exactly which part of their product each gap
threatens. Produce a concise, evidence-backed report with a prioritized
30-day plan.

This skill audits the **engineering system**, not individual engineers. Never
rank, blame, or name people in findings.

## Non-negotiable rules

- **Read-only.** Never edit, delete, or write inside the audited repository.
  Do not run the repo's own write-capable scripts (migrations, deploy, seed).
  If the user asks for remediation, stop and get explicit authorization first.
- **Evidence or it didn't happen.** Every finding cites a file path, line,
  config value, command output, or GitHub API result. No evidence → the
  control is **Not Verified**, never a confirmed failure.
- **Secrets and PII are never quoted.** Report location and type only
  ("`config/settings.py:42`, looks like a live AWS access key, `AKIA…`
  prefix"). Never paste the full value or real personal data into the report.
- **No aggregate score, ever — not even as counts framed like one.** Report
  per-control states only. Do not synthesize an overall number, grade, or
  percentage. Per-feature state counts (e.g. "2 Red, 1 Amber") are allowed
  as a glanceable summary, but never as totals, percentages, or anything
  that invites ranking features against each other — one Red can outweigh
  five Greens and the surrounding prose must make that clear, not the counts.
- **Scale to context.** The same missing control can be Amber for a small
  internal tool and Red for a customer-facing service handling personal
  data. Use the intake answers to calibrate every Amber/Red call.
- **Cap the plan at 5 actions.** The 30-day plan never exceeds five items.
- **Every control is accounted for.** Each control ID in
  `references/audit-controls.md` must appear exactly once in the report:
  either inside a feature section with a state and evidence, or in a single
  explicit "Controls not reached this pass" list at the end. A control that
  appears nowhere is a coverage bug, not a judgment call — this is what
  keeps repeat runs comparable.
- **One audit, one report — no cross-project references.** Never name or
  compare against another audited repository inside a report, even one
  from the same organization. Each report must stand alone as a
  confidential, self-contained deliverable for that project's owner.
  Cross-project patterns you notice (e.g., the same practice recurring
  across audits) are useful to mention to the person who requested the
  audits, but do not belong inside any individual project's report.

## Workflow

### 1. Check for a previous audit, then confirm scope

**Re-audit check first:** look for an existing `<repo-name>-audit-*` sibling
directory (or ask where previous reports live if the user mentions a
re-audit). If one exists, offer **re-audit mode**: read the previous
`audit-report.html` and `gap-register.html`, and in this run mark every
previous gap as **Fixed / Unchanged / Regressed** (with fresh evidence for
each verdict) plus any **New** findings, and lead the new report with a
"Changes since last audit (<date>)" section. A re-audit still covers all
controls — it is a full audit plus the comparison, not just a diff.
**If the control set has grown since the previous audit** (new control IDs
that didn't exist at that audit's date — check `criteria.html` from the
prior run), label findings from those controls **"New (criteria
expanded)"**, distinct from plain "New" findings in previously-existing
controls. Add one sentence to the "Changes since last audit" section:
"This audit applies N controls added since the previous audit; findings
from those controls reflect expanded criteria, not regression."

**Scope confirmation (one question, after a quick look, not five before):**
do a fast inventory glance first (README, manifest, function/route names),
then present a single confirm-or-correct summary, e.g.: "This looks like a
customer-facing testimonial SaaS handling personal data and payments,
deployed via a third-party platform, with no externally-consumed API —
correct? And is the default report location `<repo>-audit-<YYYY-MM-DD>/`
next to the repo OK?" Fold in two inferred clauses along with the product
profile: whether anything external consumes the project's API (published
SDK, API docs, versioned `/v1/`-style routes suggest yes; nothing suggests
internal-only — this scopes domain 12) and whether the project handles
PII/retention obligations (inferred from schema/model fields — this scopes
domain 14). One answer calibrates the whole audit. If the user says "skip"
or doesn't correct it, proceed with the inferred profile and label it an
**assumption** in the report.

If the repo is on GitHub and `gh` is authenticated (`gh auth status`), run
the read-only GitHub checks by default; mention in the same confirmation
message that you'll do so, so the user can decline. If `gh` is unavailable
or declined, mark those controls Not Verified.

### 2. Inventory, including product features

Identify, without deep-reading yet:
- Languages, frameworks, package manifests, lockfiles.
- Test directories/frameworks, CI/CD config (`.github/workflows`, etc.).
- Infrastructure-as-code, Dockerfiles, deployment config.
- Documentation (README, ADRs, runbooks, CONTRIBUTING).
- `.git` history depth and recent commit activity.

Exclude vendored/generated/build/dependency directories (`node_modules`,
`dist`, `.venv`, lockfile internals) from line-by-line inspection — note
their presence, don't read them.

Also identify the **product's feature areas** — the things a non-engineer
would recognize as parts of the product, not code modules. Infer these from
route/API structure, background-job or edge-function names, database
schema/table names, and the README. Typical shapes: "Authentication",
"Payments/Billing", "[Core domain object] management" (e.g. quotes, orders,
testimonials), "Admin/Invite/Access control", "Deployment & infra" (always
include this one — it's where CI/CD, environments, and rollback findings
land even though it isn't a user-facing feature). Aim for roughly 4-7
feature areas — enough to be specific, few enough to stay readable.

### 3. Inspect evidence by domain, mapped to features

Work through `references/audit-controls.md` domain by domain to make sure
every control is covered. For each control: search for the evidence it
requires, cite what you found (or explicitly note you could not access it),
and note **which feature area(s) it belongs to** as you go — a single
control's evidence often applies to more than one feature (e.g., "no error
tracking" affects every feature that runs in production).

Do not conclude beyond what the evidence supports.

**Read the code for the highest-risk functions, don't just confirm they
exist.** Listing filenames ("a `payments-webhook` function exists") is not
evidence of a control — it only tells you what to check next. For each
feature area, open the source of its most security- or money-relevant
entry points (payment/webhook handlers, auth/admin actions, file upload,
anything issuing or validating a token/invite link) and verify: is auth
actually checked before the sensitive action, not just present somewhere in
the file; are signatures/tokens verified with real cryptographic checks
rather than a stub; do tokens expire, or are they valid indefinitely; are
errors surfaced or silently swallowed. Budget this for maybe 5-10 functions
per audit, prioritized by what a feature's own risk profile calls for —
you cannot read every file, but "not individually read at this pass" is an
honest Not Verified for what's left, not an excuse to skip the highest-risk
ones. **Domains 11–14 are evidence-by-grep and do not expand this budget** —
the sole exception is control 14.2 (deletion actually deletes), which may
claim one of the 5-10 slots when the project handles PII, since verifying
it requires reading the deletion flow's source.

**Run a lockfile-only dependency vulnerability scan by default** — it is
read-only and requires no installation: `npm audit --package-lock-only`,
`pnpm audit --lockfile-only` (or plain `pnpm audit` if lockfile-only is
unsupported in the installed version), `pip-audit -r requirements.txt
--dry-run`, `cargo audit`, `bundle audit` — whichever fits the ecosystem.
If the ecosystem has no scannable lockfile (e.g., Deno URL imports with no
lock), say so explicitly in the report under control 6.1 as a structural
limitation, not a silent skip.

If GitHub checks were approved, run them read-only via `gh api` /
`gh pr list` / `gh repo view` (see `references/audit-controls.md` domain 3
for the exact checks: branch protection, PR reviews, CI-required, plus repo
visibility and whether Dependabot alerts / secret scanning are enabled).
Any `gh` failure → fall back to Not Verified, do not error out the audit.
GitHub-check findings generally belong under the "Deployment & infra"
feature area unless they're scoped to a specific feature's code path.

### 4. Assess

Assign each control Green / Amber / Red / Not Verified / Not Applicable
per the thresholds in `references/audit-controls.md`. Apply the risk
calibration from intake. State Not Applicable reasons explicitly.

**Exception:** a live-looking committed secret or real personal data is
always Red and always an immediate blocker, regardless of project risk
profile.

### 5. Prioritize within each feature

Within each feature area, order its findings using the risk priority from
most to least urgent:
1. Security, privacy, secrets, sensitive-data exposure (includes a Red on
   control 14.2 — data that should have been deleted but wasn't).
2. Missing/unreliable backup, recovery, or rollback.
3. Uncontrolled production access.
4. Unreviewed changes or missing CI safeguards.
5. Missing tests or performance safeguards around critical business
   behavior (controls 5.x and 11.1-11.3).
6. Unclear ownership and operational responsibility.
7. Documentation and maintainability — also where planned-improvement-tier
   findings land: controls 12.x (API contract), 4.7 (type safety), 5.4
   (integration coverage), 9.3 (alerting), and 11.4 (caching).

Separate immediate blockers (secrets, active exposure) from planned
improvements. Across features, the feature with the most severe findings
(by this same order) leads the executive summary and the 30-day plan.

### 6. Produce outputs

Write **self-contained HTML** files to the location chosen at intake, using
`assets/audit-report-template.html`, `assets/gap-register-template.html`,
`assets/index-template.html`, and `assets/criteria-template.html` as the
structure/styling to fill in (`index.html`, `audit-report.html`,
`gap-register.html`, `criteria.html`). `index.html` is the entry point —
link to it when telling the user where the audit lives. No external
CSS/JS/fonts — everything inline, so the files open standalone in a
browser. These reports may contain confidential client information, so do
not publish them as hosted Artifacts; write them only to local disk.

**The four templates are the single source of truth for page structure,
navigation, and styling** — follow their section order, nav bar, anchors,
and interactive elements exactly; do not invent a different layout. In
brief (details live in the templates themselves): reports are structured
by feature area, not domain number; the index page is an action dashboard
(blockers, severity counts, checklist of the 5 plan actions); the 30-day
plan appears before the feature detail; every control citation uses a
short `(control n.n)` tag that is also a `<details>` toggle showing that
control's Green/Red criteria inline; feature sections open with a static,
worst-first state count (no totals/percentages); `criteria.html` is a
per-audit snapshot of all ~35 controls' thresholds, generated fresh each
run so it reflects the criteria as they stood at that audit's date; gap
IDs and findings cross-link between all four pages.

**These reports are shared deliverables read by project owners**, not just
your own working notes — write the standing note in the report header
exactly as the template shows it: findings marked Not Verified or Red can
be revised if the owner holds evidence this audit couldn't access (see the
amend procedure in step 7). This is lightweight contestability, not an
invitation to relitigate every state — the criteria are fixed reference
text, only the evidence behind a specific finding is up for correction.

Also required regardless of layout:
- Do not reference other audited repositories anywhere in the report.
- State the inspection boundary explicitly: what was checked, what wasn't
  accessible, whether GitHub checks and the dependency scan ran. Always
  include this standing line: "Accessibility and internationalization
  were not assessed; they require browser-based testing outside this
  audit's static-analysis scope."
- Account for every control ID (see non-negotiable rules).

### 7. Stop — and how to amend later

Do not modify the audited repository. If the user wants to act on findings,
confirm explicitly what they want changed before touching any files.

**When answers to the report's open questions arrive** (this session or a
later one): update the existing report files in place — resolve the
affected Not Verified controls to real states with the answer as cited
evidence ("per project owner, <date>"), move any confirmed gaps into the
gap register, and add an "Amended <date> after owner confirmation" note
under the report header. Do not leave answered questions sitting in the
questions section.

## References

- `references/audit-controls.md` — the 10 domains, ~35 controls, evidence
  required, and Green/Red thresholds for each.

## Assets

- `assets/index-template.html` — entry-point action dashboard linking the other three pages.
- `assets/audit-report-template.html` — report structure to fill in (HTML, self-contained).
- `assets/gap-register-template.html` — gap register table structure (HTML, self-contained).
- `assets/criteria-template.html` — per-audit snapshot of all control thresholds (HTML, self-contained).
