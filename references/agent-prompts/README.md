# Analyst and reviewer prompts

Templates for the sub-agents used in steps 6 and 9 of the full audit. Fill the placeholders, then give the text to a fresh agent (one agent per file). Every prompt is read-only and asks for findings in the schema in `../findings-schema.md`.

Placeholders:
- `{{REPO_PATH}}` absolute path of the audited repository
- `{{REF}}` the remote-tracking ref to read (for example `origin/main`), never the possibly stale working tree
- `{{SCOPE_PATHS}}` the directories or modules in scope
- `{{FLOWS}}` the critical flows from the system context
- `{{CLAIMS}}` the numbered findings to test (reviewer only)

Rules that apply to all of them:
- Read code only with `git -C {{REPO_PATH}} show {{REF}}:<path>` and `git -C {{REPO_PATH}} grep -n <pattern> {{REF}} -- <paths>`.
- Never edit, run scripts or migrations, or use network or cloud tools.
- Never print secrets, tokens or personal data.
- Report only what the code proves; mark each finding `Confirmed` or `Suspected` and cite file and line.
- Keep the report under 1000 words. List what was correctly protected and what could not be verified.

Files:
- `public-route-token-check.md`
- `tenant-scoping-map.md`
- `transactional-integrity.md`
- `independent-review.md`
- `injection-and-authn-sweep.md` (SQL and command injection, and missing authentication on routes, for any web framework)

Agent reports are model output. The lead auditor spot-checks every Critical claim before it enters the register, and renumbers colliding ids.

The examples in these prompts (decorators, ORM transactions) come from one framework. Translate them to the stack you are auditing; the questions matter, not the syntax.
