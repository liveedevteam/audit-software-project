# audit-software-project

[![npm version](https://img.shields.io/npm/v/audit-software-project.svg)](https://www.npmjs.com/package/audit-software-project)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-5A32FB.svg)](https://claude.com/claude-code)

An evidence-based engineering audit skill for [Claude Code](https://claude.com/claude-code).

Point it at a local repository and it inspects the codebase across 13
engineering domains (~47 controls) — ownership, source-control safeguards,
code quality, testing, security, CI/CD, architecture/trust boundaries,
operations, documentation, performance, API contracts, and data
lifecycle/retention — then produces a self-contained HTML report organized
by **product feature area**, not abstract domain number, with a prioritized
30-day improvement plan capped at five actions.

**[View a sample report →](https://liveedevteam.github.io/audit-software-project/sample-report/)**
(fictional project, invented findings — illustrates the output format only;
real audit reports contain confidential findings and are never published)

## What it does

- **Read-only by default.** Never edits, deletes, or writes inside the
  audited repository unless the user explicitly authorizes remediation.
- **Evidence or it didn't happen.** Every finding cites a file path, line,
  config value, command output, or GitHub API result. No evidence means
  the control is marked **Not Verified**, never a confirmed failure.
- **No aggregate score.** Reports states per control
  (Green / Amber / Red / Not Verified / Not Applicable) — never a single
  number, grade, or percentage that invites ranking features against each
  other.
- **Scales to context.** The same missing control can be Amber for a small
  internal tool and Red for a customer-facing service handling personal
  data.
- **Secrets and PII are never quoted** in reports — location and type only.
- **Re-audit mode.** Re-running against a repo with a previous audit marks
  every prior gap Fixed / Unchanged / Regressed, plus any New findings,
  and clearly separates genuinely new gaps from findings that only exist
  because the control set itself grew since the last run.
- **Audits the engineering system, not individual engineers.** Findings
  are never used to rank, blame, or name people.

## Install

```bash
npx audit-software-project
```

This copies `SKILL.md`, `references/`, and `assets/` into
`~/.claude/skills/audit-software-project/`. Safe to re-run any time to
update to the latest published version — it overwrites the existing
install. Claude Code picks up the skill on the next session.

Alternatively, clone the repo directly:

```bash
git clone https://github.com/liveedevteam/audit-software-project.git \
  ~/.claude/skills/audit-software-project
```

## Use

Ask Claude Code to audit a local repository, for example:

- "Audit this codebase and give me a 30-day improvement plan."
- "Is this repository ready for production?"
- "Re-audit this project after our remediation work."

Claude will do a quick inventory pass, confirm one scope-calibrating
question (risk profile, data sensitivity, external API consumers, etc.),
then work through the control set and write the report to
`<repo-name>-audit-<date>/` next to the repository — `index.html` is the
entry point.

## Structure

```
SKILL.md                          # workflow the skill follows
references/audit-controls.md      # the full control set: evidence, Green/Red thresholds
assets/index-template.html        # report entry-point / action dashboard
assets/audit-report-template.html # main report structure
assets/gap-register-template.html # gap register table
assets/criteria-template.html     # per-audit snapshot of all control thresholds
```

## Roadmap

**Now — prerequisite to everything below:**
- Run a full pilot audit (and ideally a re-audit) against a real
  repository. The 47-control set has been reviewed and stress-tested on
  paper but not yet exercised end to end; pilot findings will likely
  reorder the items below before any of them are worth committing to.

**Next (small, concrete):**
- `--path` flag on the CLI, to install into a custom skills directory
  instead of assuming `~/.claude/skills/`.
- Stamp each generated report with the control-set version it ran
  against (the npm package version doubles as this identifier for free)
  — strengthens the re-audit "New (criteria expanded)" comparability
  story already built into the skill.

**Later (needs more design first):**
- Optional `.auditrc` to persist a repo's risk-profile answers across
  repeat audits, so the same calibration question isn't re-asked every
  re-audit run.
- Broaden the handful of language-specific evidence patterns (currently
  JS/Python-leaning — controls like 8.4 injection surface and 11.1–11.2
  query patterns) to cover Go, Rust, and Java idioms. Most controls are
  already language-neutral; this only affects the code-pattern-grep ones.

**Research questions, not yet roadmapped:**
- Accessibility/i18n (the deliberately-unused domain 13 slot) — blocked
  on wiring in real browser-based tooling (e.g. axe-core), since static
  analysis alone can't verify this confidently.
- Cross-repo trend/rollup views for teams auditing multiple projects —
  in tension with the skill's "one audit, one report, no cross-project
  references" confidentiality rule, so needs a data-location design
  decision before it's buildable at all.

Have a request or found a gap? Open an issue on the
[GitHub repo](https://github.com/liveedevteam/audit-software-project/issues).

## License

MIT — see [LICENSE](LICENSE).
