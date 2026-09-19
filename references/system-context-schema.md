# system-context.json

Produced in full-mode step 3. It drives the overview page and the C4 level 1 and 2 diagrams built by `scripts/audit_site.py`. A complete fictional example is `assets/sample/system-context.sample.json`.

All text is plain text (the generator escapes it). Anything you could not confirm goes in `unconfirmed`, not in the diagram text as if it were fact. Every component that has findings lists them in `finding_ids`; the generator draws a red tag (amber for Medium or Low) and links the pill to the register. Unknown finding ids are rejected.

| Field | Meaning |
|---|---|
| `project`, `description` | Name and a short description of what the platform is and who uses it |
| `timing_note` | Optional deadline or window that affects remediation planning |
| `stats` | List of `{value, label}` shown as cards |
| `actors` | Level 1 people or groups: `{id, name, lines[], finding_ids[]}` (up to 4 fit well) |
| `actor_edges` | `{from: actor id, label}`, drawn actor to system |
| `system` | The system as one box: `{name, lines[], finding_ids[]}` |
| `externals` | External systems: `{id, name, note, finding_ids[]}` (shown in level 1 and in level 2) |
| `containers` | Level 2 building blocks: `{id, name, lines[], placement, tier, finding_ids[]}`. `placement` is `client` (left column, users reach it), `inside` (inside the runtime boundary, arranged in rows by `tier` 0, 1, 2 ...) or `outside` (left column below the clients, for CI/CD and observability) |
| `container_edges` | `{from, to, label, dashed}` between container ids. Edges from an `outside` component point at the boundary edge |
| `external_caller` | Id of the container that calls the external systems. Put it in tier 0 so the connector runs along the top of the boundary |
| `boundary_label`, `client_label` | Captions for the boundary and the client column |
| `container_caption` | Optional extra caption under the level 2 diagram |
| `domains` | `{name, covers, modules, finding_ids[]}` business areas |
| `stack` | `{layer, tech}` |
| `environments` | `{name, detail, notes}` per environment |
| `deployment_note`, `deployment_steps` | Pipeline steps: `{name, lines[], finding_ids[]}` |
| `flows` | Critical business flows: `{name, what, status, finding_ids[]}`; `status` says how far the audit traced it |
| `access_model` | A short paragraph on authentication, authorization and tenancy |
| `unconfirmed` | List of facts that were not confirmed (hosting, network paths, and so on) |

Rules: use `lines` of about 30 characters; no secrets, hostnames of internal systems, account ids or personal data; cite only what evidence supports.

Field details
- `stats[].value`: a string or a number; it is shown as text.
- `external_caller`: optional. Leave it out when `externals` is empty. When set, put that container in tier 0.
- `containers[].tier`: integers starting at 0; boxes with the same tier share a row. Only used for `inside` containers.
- `flows[].status`: free text saying how far the flow was traced, for example "Traced (transactions)" or "Not yet traced".
- `actor_edges[].label`: optional; defaults to "uses".
- Finding ids in any `finding_ids` must exist in `findings.json`; the generator rejects unknown ids.
