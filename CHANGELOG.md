# Changelog

## 2.0.0

First stable 2.x release. Install with `npx audit-software-project`.

- Quick mode (repository audit, 47 controls, four HTML pages, 30-day plan) is stable.
- Full mode (everything added in 2.0.0-alpha.0 below) ships as **experimental**: it runs end to end and was dry-run by a fresh session on 2026-09-19, but some parts are not built or only tested on one stack or one cloud account. See `STATUS.md`.
- Docs: full mode relabelled from "alpha" to "experimental" in README.md and SKILL.md; STATUS.md updated to reflect what is published.

Known limits: no gap-register or criteria pages for full mode, no scope intake, no remediation or ticket drafts, no full-mode re-audit comparison, agent prompts exercised only on a JavaScript/TypeScript backend with an ORM.

## 2.0.0-alpha.0

Alpha of the full audit mode. Not recommended for production use yet; install with `npx audit-software-project@alpha`.

Added
- `--mode full`: an 11-step audit method (scope, evidence, system context, automated assistance, AI review, business-flow validation, findings, risk assessment, independent false-positive review, report, remediation plan) in `references/full-audit-method.md`.
- `references/guardrails.md`: read-only, production read-only, no secrets or personal data in outputs, no people named, nothing sent or published without approval.
- Findings schema (`references/findings-schema.md`, `findings.schema.json`) and `scripts/validate_findings.py`.
- `scripts/aws_readonly_inventory.sh` with a guard that allows only describe/list/get/head calls and refuses secret-returning operations.
- `scripts/secret_hunt.sh` (locations and types only), `scripts/dependency_scan.sh` (lockfile only), `scripts/github_checks.sh` (GET requests only).
- Read-only sub-agent prompt templates and a mandatory independent review stage.
- `scripts/audit_site.py`: builds the overview (generated C4 level 1 and 2 diagrams), audit report and findings register from `findings.json`, `system-context.json` and `audit.json`.
- Fictional sample inputs in `assets/sample/`.
- Installer flag `--path <skills-dir>`.

Changed after a fresh-session dry run: cloud guard uses an explicit operation allowlist and has `--self-test`; new `self-review` verification method; register wording derived from verification data; validator checks control ids and `human_approved`; new `references/full-mode-artifacts.md`, sample working files and an injection and authentication prompt; consistent control counts (47 across 13 domains).

Known limits: see `STATUS.md` (no gap-register or criteria pages for full mode, no scope intake, no ticket drafts, not yet dry-run by a fresh session).

## 1.0.1

Quick repository audit (47 controls, four HTML pages, 30-day plan).
