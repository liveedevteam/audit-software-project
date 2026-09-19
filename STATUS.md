# Status: v2.0.0-alpha.0 (skeleton)

This is a working skeleton, not a finished release. Nothing here has been published to npm or GitHub.

## Built and tested
- Full-mode method (`references/full-audit-method.md`), guardrails, findings schema (markdown and JSON Schema), four sub-agent prompt templates.
- `scripts/aws_readonly_inventory.sh`: guard refuses non-read-only calls and secret-returning `get-*` calls (tested with eight refused cases). The inventory ran end to end once against one real account (single region, 16 regional files plus S3 metadata, no error stubs, no secret-shaped strings in the output); other regions, accounts and services are untested.
- `scripts/secret_hunt.sh`: prints path:line and type only (tested: fake key and URL password are detected, values never printed).
- `scripts/dependency_scan.sh`: lockfile-only scan from a git ref (npm path tested only for the no-lockfile branch here; the npm audit path was used manually in the pilot audit).
- `scripts/github_checks.sh`: read-only GET requests (run against one public repository).
- `scripts/validate_findings.py`: tested on the sample and on a deliberately broken file (secret-looking evidence, bad enum, bad id, missing field, unknown supersedes id are all caught).
- `scripts/build_findings_register.py`: renders the sample findings.
- `scripts/audit_site.py`: builds the overview (C4 level 1 and 2 generated from `system-context.json`, domains, stack, environments, deployment flow, critical flows, dashboard), audit report and findings register from three JSON files; validates findings first and rejects unknown finding ids. Also run on the real pilot audit (39 findings, 15 questions, full system context): validator passed, links resolve, diagrams readable after shortening a few box labels (generator limit: box text wider than about 28 characters can overrun narrow boxes). Tested on the fictional sample: links resolve, SVGs are well-formed, layout checked in a browser (one crossing arrow found and fixed by routing outside-boundary components to the boundary edge).
- Installer (`bin/cli.js`) copies SKILL.md, references, assets and scripts; supports `--path`.

## Not built yet
- Layout limits of the diagram generator: level 2 assumes up to about 3 tiers of 3 to 4 boxes and one external caller in tier 0; unusual topologies may need manual `container_edges` tuning. Only the fictional sample and the pilot audit shape have been rendered.
- Control-based gap register and criteria pages for full mode (they remain quick-mode templates; the findings register replaces the gap register in full mode).
- `scope.json` intake questionnaire and schema.
- Jira and chat evidence collection is described in the method but has no script (it relies on whatever connectors the session has, always read-only).
- Remediation draft generator (`remediation.md`) and ticket text templates.
- A test run of the whole flow by a fresh session on a small non-sensitive repository.
- Generalisation review of the agent prompts for stacks other than a JavaScript/TypeScript backend with an ORM (the prompts are written as patterns, but only that stack has been exercised).
- Re-audit comparison for full mode (fixed, unchanged, regressed) using finding ids.

## Fresh-session dry run (2026-09-19)
A fresh agent, given only the installed skill (from the packed tarball) and a small fictional repository with planted problems, ran full mode without cloud, GitHub, ticket or sub-agent access. It completed the repository-only slice, found the planted problems (no authentication, injection, missing tenant check, non-atomic writes, an example key, thin tests) and logged 19 friction items in about 3 minutes of agent time (a new person should budget 40 to 60 minutes). Fixed since: an explicit-operation allowlist and a safe `--self-test` for the cloud guard (the agent's own test of the guard had reached the cloud CLI once, harmlessly), consistent control counts, the step 10 contradiction, formats for the working files, a `self-review` verification method with a register label derived from the real verification data, `human_approved` and control-id validation, a framework-neutral injection and authentication prompt, requirements, no bytecode in the package, STATUS.md installed. Not exercised: the cloud inventory on a second account, GitHub checks against a private repository, the independent-review step with real sub-agents on this repository.

## Before publishing
Done (2026-09-19): package contents checked (35 files, 65.3 kB) and searched for project-specific data (none); README requirements and CHANGELOG added; installer tested into a temporary directory.
Remaining:
1. Optional for the alpha, required for a stable 2.0.0: a dry run by a fresh session on a small non-sensitive repository, fixing what it reveals.
2. Log in to npm (`npm login`, 2FA) and publish the alpha under a dist-tag so `latest` stays 1.0.1: `npm publish --tag alpha`. Install with `npx audit-software-project@alpha`. A published version number cannot be reused.
3. Push the source to the GitHub repository and tag `v2.0.0-alpha.0` (the local folder is not a git checkout).
4. Update the team Slack message once published.
