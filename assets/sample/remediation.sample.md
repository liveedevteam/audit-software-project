# Remediation drafts (fictional sample)

Status: DRAFT. Nothing has been created in any ticket system or sent anywhere.

## Action 1: remove the exposed diagnostics route
### R1. Remove the diagnostics route and rotate the secret
- Priority: Highest (proposed) | Effort: Small
- Findings: SEC-001
- Owner: _(team to assign)_ | Target date: _(team to set)_

Steps: remove the route; stop putting secrets in error text; rotate the secret.
Acceptance criteria: the route returns 404 in every environment; a test checks it stays absent.

## Coverage
| Finding | Task |
|---|---|
| SEC-001 | R1 |

## Approval needed before anything leaves this file
Creating tickets, posting to chat, opening pull requests.
