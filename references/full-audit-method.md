# Full audit method (full mode)

Use this mode when the requester wants a full software audit beyond the static repository review: infrastructure, environments, tickets, business-flow validation, independent review and a remediation chain. The quick mode in `SKILL.md` stays the default for a fast repository audit.

## Working without cloud access, tickets or sub-agents

- **No access means Not Verified, then continue.** If a tool, account or connector is missing (cloud CLI, GitHub, tickets, chat), skip that evidence step, record it under `audit.json` `boundary.not_checked` with the reason, and carry on with what you can read. A missing source is never a finding.
- **No sub-agents available?** Do the analyst passes yourself using `references/agent-prompts/`, then do a clearly separate second pass that tries to refute your own findings. Record that pass as `verification.method: self-review`. Use `lead` only for what you verified directly in the code or configuration, and `independent-review` only when a separate agent or a human actually did the review. State this limitation in `boundary.not_checked`.
- **Formats.** The optional working files (`scope.json`, the evidence index, `flow-validation.md`, `remediation.md`) are described in `full-mode-artifacts.md`.

Every step lists what goes in, what comes out, and the gate that must pass before the next step. Steps 1 to 10 are read-only. Step 11 produces drafts only.

## Step 1. Scope
- Input: the requester's scope statement.
- Output: `scope.json` with `project`, `audit_type`, `in_scope` (frontend, backend, database, infrastructure, CI/CD, security, testing, documentation), `environments` (each `dev`, `uat`, `prd` with an access level: `none`, `read-only`), `out_of_scope` (default: penetration testing against production, third-party internal systems), `authorization` (who approved cloud, ticket and chat access) and `risk_profile` (customer-facing, data sensitivity, external API consumers).
- Gate: the requester confirmed the scope once. Production access is `read-only` at most. Anything not listed is out of scope.

## Step 2. Collect evidence
- Use only the scripts in `scripts/` and read-only commands. Prefer the remote-tracking branch over a possibly stale checkout (`git show origin/<default>:path`).
- Collect: repository facts, GitHub settings, dependency scan, secret-pattern hunt, cloud inventory (metadata only), tickets and comments, chat search for project identity.
- Output: `evidence/` (raw command outputs with secret values removed) and an evidence index that gives every item an id.
- Gate: no secret values or personal data written to disk. Cloud calls went through the guarded wrapper.

## Step 3. Understand the system
- Output: `system-context.json` (architecture, component map, database and data flow, external integrations, deployment flow, critical business flows, environments) and the C4 level 1 and 2 diagrams built from it.
- Repository documents are inputs, not truth: check them against code and metadata, and record what is out of date.
- Gate: each component and integration in the diagrams is grounded in something you actually read (a file, command output or configuration value); anything you could not confirm goes in `unconfirmed` and is labelled "not confirmed".

## Step 4. Automated assistance
- Run the dependency scan, secret hunt, static pattern greps (public routes, string-built SQL, `exec`, disabled TLS validation) and infrastructure checks. Automated output is a lead, not a finding.

## Step 5. AI review, human approval
- An AI reviewer reads the code behind each lead. The default is that a human approves the findings before they leave the audit folder. If the requester explicitly replaces human approval with an AI review, keep the label "AI-proposed, not human-approved" on every finding and page.

## Step 6. Validate critical business flows
- Pick the flows from step 3 (money, identity, regulated records, data deletion, external signing). For each flow, use the agent prompts in `references/agent-prompts/` to answer: who can call it, is the caller checked, is the tenant checked, is it atomic, what happens on failure.
- Output: `flow-validation.md` with a table per flow and the findings it produced.
- Gate: each analyst agent returns findings in the schema, cites file and line, and separates Confirmed from Suspected.

## Step 7. Create findings
- One finding per issue, in `findings.json` (see `findings-schema.md`). Fields: id, title, domain, severity, evidence, observation, impact, recommendation, effort, confidence, verification.
- IDs are `<DOMAIN>-<NNN>`, unique across the audit. Renumber collisions from analyst agents.

## Step 8. Risk assessment
- Severity uses impact and reachability together: `Critical` (exploitable by an unauthenticated or any-authenticated actor with data or account impact), `High`, `Medium`, `Low`. State reachability in the finding (unauthenticated, any authenticated user, internal only).
- Calibrate to the risk profile from step 1. Do not produce an overall score.

## Step 9. Verification and false-positive review
- A separate reviewer agent, given only the claims and the code paths, tries to refute each finding: it looks for global guards, interceptors, database extensions, later checks and environment gating.
- Verdicts: `confirmed`, `partially-confirmed` (say what was overstated), `refuted`. Downgrade or drop accordingly and record the verdict in `verification`.
- The lead auditor re-verifies every Critical finding directly. Stale claims from tickets are checked against current code and marked `fixed` or `still-true`.

## Step 10. Generate the report
- `scripts/audit_site.py` renders three pages from `findings.json`, `system-context.json` and `audit.json`: the overview (with C4 diagrams), the audit report and the findings register. The control-based gap register and criteria pages exist only in quick mode; do not expect them in full mode. State the inspection boundary, what was not checked, and the standing accessibility line.

## Step 11. Remediation plan
- Chain: Audit finding, Recommendation, Remediation task, Ticket, Developer, Pull request.
- Output: `remediation.md` with tasks grouped into at most 5 plan actions, each linked to finding ids. Ticket text is a draft.
- Gate: never create tickets, post comments or send messages without the requester's explicit approval. Fix diffs are prepared in a scratch copy and never applied to the audited repository unless the requester asks.
