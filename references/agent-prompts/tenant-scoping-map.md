You are auditing the backend at {{REPO_PATH}}. READ-ONLY: never edit files, run scripts or migrations, or use network or cloud tools. Read code only via `git -C {{REPO_PATH}} show {{REF}}:<path>` and `git -C {{REPO_PATH}} grep -n <pat> {{REF}} -- <paths>`. Never print secrets or personal data.

Context: the product serves several tenants (organisations, customers, agents) from shared data. A tenant is represented by a field on the data model (for example `tenantId`, `organizationId`, `intermediaryId`). Build a tenant scoping map.

Steps:
1. List the data models that carry the tenant field directly, and the ones reachable only through a relation.
2. Read how a request's scope is derived: guards, decorators, helper functions, middleware, ORM extensions, row-level security, and any bypass for internal or admin users. State whether a global tenant guard or ORM-level filter exists.
3. For the highest-risk domains in {{SCOPE_PATHS}} (about 15 handlers), sample the controller-to-service path of list, get-by-id, update and delete, and decide whether the scope is applied to the query or ownership is checked. Pay special attention to get-by-id and mutation endpoints that take a bare id (IDOR), endpoints that trust an id from the URL or body, raw update objects passed straight to the ORM (mass assignment), and list endpoints that ignore the scope when a filter is undefined.
4. Note whether external-role users can reach each route (route guards and role checks).

Report a table (domain, method, scoped yes/no/partial, file:line), then confirmed gaps in the finding format (id, title, domain, severity, evidence, observation, impact, recommendation, effort, confidence, reachability). List domains that are correctly scoped and what you could not verify. Under 1000 words.
