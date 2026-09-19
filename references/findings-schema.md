# Findings schema

`findings.json` is a JSON object: `{"project": "...", "date": "YYYY-MM-DD", "findings": [ ... ]}`. Validate with `scripts/validate_findings.py`. The machine-readable version is `findings.schema.json` in this folder.

Each finding:

| Field | Required | Notes |
|---|---|---|
| `id` | yes | `<DOMAIN>-<NNN>`, uppercase letters then three digits, unique in the file (for example `SEC-011`, `DB-003`) |
| `title` | yes | One line, states the problem, not the fix |
| `domain` | yes | Free text such as `Security / Access control`, `Database / Data integrity`, `AWS / Network`, `CI/CD` |
| `severity` | yes | `Critical`, `High`, `Medium`, `Low` |
| `evidence` | yes | Non-empty list of citations: file and line range, config value, command, API result. Never a secret value |
| `observation` | yes | What was seen |
| `impact` | yes | What can go wrong, for whom |
| `recommendation` | yes | The change that removes the risk |
| `effort` | yes | `Small`, `Medium`, `Large` |
| `confidence` | yes | `Confirmed` or `Suspected` |
| `reachability` | no | `unauthenticated`, `any-authenticated`, `internal`, `n/a` |
| `verification` | no | Object: `method`, `verdict` and `note`. `method`: `lead` (the auditor verified it directly in code or configuration), `independent-review` (a separate agent or a human reviewed it), `self-review` (a second pass by the same session, not independent), `analyst` (reported by an analyst, not separately reviewed), `automated` (a script or scanner), `metadata` (read from platform or settings metadata). `verdict`: `confirmed`, `partially-confirmed`, `refuted`, `not-reviewed` |
| `control` | no | Related control id from `audit-controls.md`, written like `8.1` (domain.control), or `ext` for findings outside the control set |
| `status` | no | `open` (default), `superseded`, `fixed` |
| `supersedes` | no | List of ids this finding replaces |
| `ticket` | no | Ticket key, once one exists |

Rules:
- Evidence lines contain locations, not content.
- `Critical` requires `reachability` and a lead verification.
- A finding whose independent verdict is `refuted` is removed from the register and listed under "Refuted" in the report.
- `Suspected` findings never carry `Critical` unless the evidence for the code path is confirmed and only the reach is unknown; say so in `note`.

Top-level `human_approved`: optional boolean. Set it to `true` only when a human has approved the findings; otherwise leave it out and the register says they are AI-proposed.

Id prefixes (2 to 6 capital letters): use one that fits, for example `SEC` security, `TEN` tenant isolation, `DB` database, `INF` infrastructure, `CICD` pipeline, `OPS` operations and reliability, `TEST` testing, `QUAL` code quality, `DEP` dependencies, `GOV` governance, `DOC` documentation. Pick a sensible prefix for anything else; the number is unique across the whole audit.

Writing evidence:
- A code finding cites file and line range: `src/orders/service.js:40-62`.
- A comment marker cites the marker: `src/bookings.js:1 (TODO: validate tenant before returning a booking)`.
- An absence finding cites what you searched and found nothing: `no CI configuration found (searched .github/workflows and common CI files)`; `no lockfile at the repository root`.
- Never cite a secret by value; cite file, line and type.
