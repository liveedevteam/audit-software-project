# audit.json

Report-level content for `scripts/audit_site.py`. A fictional example is `assets/sample/audit.sample.json`. Text is plain text (escaped by the generator).

| Field | Meaning |
|---|---|
| `project`, `date`, `auditor` | Name, `YYYY-MM-DD`, and who or what produced the audit (say "AI-assisted audit" when applicable) |
| `summary` | List of short paragraphs. Lead with the area holding the most severe findings. No aggregate score |
| `blockers` | Finding ids that need action before anything else ships. Rule of thumb: every Critical finding whose `reachability` is `unauthenticated`, and any live secret or active data exposure. May be an empty list. Each id must exist in `findings.json` |
| `plan` | At most five actions, ordered by severity: `{area, action, finding_ids[]}`. Only the first five are rendered |
| `risk_context` | The risk profile from scope confirmation (customer-facing, data sensitivity, hosting, external API consumers) |
| `questions` | Open questions for humans: `{question, area}` |
| `not_reached` | Things not done this pass |
| `boundary` | `{checked, not_checked, tools}`: state what was and was not inspected, and which scripts ran |

The report always ends with the standing line that accessibility and internationalization were not assessed.

Approval labelling: findings carry "AI-proposed, not human-approved" unless `findings.json` sets `"human_approved": true`.
