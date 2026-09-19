You are auditing the backend at {{REPO_PATH}}. READ-ONLY: never edit files, run scripts or migrations, or use network or cloud tools. Read code only via `git -C {{REPO_PATH}} show {{REF}}:<path>` and `git -C {{REPO_PATH}} grep -n <pat> {{REF}} -- <paths>`. Never print secrets, tokens or personal data.

Context: some routes are marked public (for example a `@Public()` decorator, a permit-all rule, or an auth middleware exclusion) so that external parties such as signers, invitees or webhook senders can reach them. Determine, handler by handler, whether each public handler actually verifies a token, signature or ownership BEFORE it reads or writes data.

Scope: {{SCOPE_PATHS}}. Start by listing every public route in scope (class-level and method-level markers), then for each answer:
- What identifier does it accept (session id, record id, token, email, path parameter)?
- Is that identifier checked against a stored, unexpired, unused token, or against the authenticated caller's ownership, before data is read or written?
- Can it be used with only a guessable or leaked id and no token? Are ids random and unguessable, and where do they leak (emails, URLs, logs, other public routes)?
- Are expired, cancelled or revoked invitations rejected?
- Does it return data about other parties, or allow enumeration (existence of an email or record)?
- Does a public route hand out a value that another public route accepts as the only credential (credential handover)?
- Are per-route rate limits applied?
- Does a webhook verify a signature in constant time, with a time window, before touching the payload?

Report a table (route, identifier, token verified yes/no/partial with file:line, risk), then the confirmed vulnerabilities in the finding format (id, title, domain, severity, evidence, observation, impact, recommendation, effort, confidence, reachability). List handlers that are correctly protected and anything you could not verify. Under 1000 words.
