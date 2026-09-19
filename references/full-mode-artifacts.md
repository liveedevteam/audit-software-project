# Working files in full mode

Optional working files, described so different sessions produce the same shapes. Fictional examples are in `assets/sample/`. None of them may contain secret values or personal data.

## scope.json (step 1)
```json
{
  "project": "Acme Booking Portal",
  "audit_type": "Full software audit",
  "in_scope": ["backend", "database", "ci-cd", "security", "testing", "documentation"],
  "environments": { "dev": "read-only", "uat": "none", "prd": "read-only" },
  "out_of_scope": ["penetration testing against production", "third-party internal systems"],
  "authorization": { "cloud": "read-only profile approved by the requester", "tickets": "none", "chat": "none" },
  "risk_profile": { "customer_facing": true, "personal_data": true, "payments": true, "external_api_consumers": false }
}
```
Environment access values: `none` or `read-only`. Anything not listed is out of scope.

## Evidence index (step 2)
A plain list in `evidence/index.md`, one line per item: an id (`E-001`), what was collected, the command or source, and the file it was saved to. Save raw outputs next to it with secret values removed. Findings may cite an evidence id in the `evidence` array (for example `E-004: rds describe-db-instances`), but the id is a convenience; the citation that matters is the file and line, configuration value or command.

## flow-validation.md (step 6)
One section per critical flow:
- Flow name and what it does (one sentence).
- A table: step or handler, who can call it, what is checked (authentication, ownership or tenant, token), atomicity (one transaction or independent writes), failure behaviour, file:line.
- Findings produced (ids) and what was correctly protected.
- What you could not trace.

## remediation.md (step 11)
At most five plan actions. For each action, one or more tasks with: id (R1, R2 ...), title, proposed priority, effort, linked finding ids, steps, acceptance criteria and notes. Owner and target date stay blank for the team. Ends with a coverage table mapping every open finding to a task. Header states that nothing has been created in any ticket system, and lists the approvals needed before anything leaves the file.

## Secret triage note
The secret hunt reports locations and types only. Triage each hit by reading the location: placeholders, test fixtures, publishable keys and documented example values (for instance the AWS documentation example key that ends in `EXAMPLE`) are not live secrets. Record them as Low, or drop them, and say why. A live-looking secret is an immediate blocker.
