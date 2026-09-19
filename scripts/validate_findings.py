#!/usr/bin/env python3
"""Validate a findings.json against the audit findings schema (standard library only).

Usage: validate_findings.py findings.json

Checks required fields, enum values, id format and uniqueness, supersedes references,
the Critical rules (reachability and a lead verification), and refuses evidence that looks like a
secret value (the audit must cite locations, never values). Exit code 0 = valid, 1 = problems.
"""
import json
import re
import sys

sys.dont_write_bytecode = True

SEVERITY = {"Critical", "High", "Medium", "Low"}
EFFORT = {"Small", "Medium", "Large"}
CONFIDENCE = {"Confirmed", "Suspected"}
REACH = {"unauthenticated", "any-authenticated", "internal", "n/a"}
METHOD = {"lead", "independent-review", "self-review", "analyst", "automated", "metadata"}
VERDICT = {"confirmed", "partially-confirmed", "refuted", "not-reviewed"}
STATUS = {"open", "superseded", "fixed"}
REQUIRED = ["id", "title", "domain", "severity", "evidence", "observation", "impact", "recommendation", "effort", "confidence"]
ID_RE = re.compile(r"^[A-Z]{2,6}-\d{3}$")
CONTROL_RE = re.compile(r"^(\d{1,2}\.\d{1,2}|ext)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Patterns that indicate a secret value was pasted into the findings.
SECRET_RES = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"\b(sk|rk)_(live|test)_[A-Za-z0-9]{10,}"), "API secret key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}"), "GitHub token"),
    (re.compile(r"xox[bpars]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{10,}"), "JWT"),
    (re.compile(r"[a-z]+://[^\s/:@]+:[^\s@]{4,}@"), "credential in URL"),
]


def check(path):
    problems = []
    try:
        data = json.load(open(path))
    except Exception as exc:  # noqa: BLE001
        return [f"cannot read {path}: {exc}"]
    if not isinstance(data, dict):
        return ["top level must be an object"]
    for key in ("project", "date", "findings"):
        if key not in data:
            problems.append(f"missing top-level field: {key}")
    if isinstance(data.get("date"), str) and not DATE_RE.match(data["date"]):
        problems.append("date must be YYYY-MM-DD")
    if "human_approved" in data and not isinstance(data["human_approved"], bool):
        problems.append("human_approved must be true or false")
    findings = data.get("findings")
    if not isinstance(findings, list):
        return problems + ["findings must be a list"]

    ids = [f.get("id") for f in findings if isinstance(f, dict)]
    for i, f in enumerate(findings):
        where = f.get("id", f"#{i}") if isinstance(f, dict) else f"#{i}"
        if not isinstance(f, dict):
            problems.append(f"{where}: finding must be an object")
            continue
        for key in REQUIRED:
            if key not in f or f[key] in ("", [], None):
                problems.append(f"{where}: missing or empty {key}")
        if "id" in f and not ID_RE.match(str(f["id"])):
            problems.append(f"{where}: id must look like SEC-011")
        if ids.count(f.get("id")) > 1:
            problems.append(f"{where}: duplicate id")
        for key, allowed in (("severity", SEVERITY), ("effort", EFFORT), ("confidence", CONFIDENCE), ("reachability", REACH), ("status", STATUS)):
            if key in f and f[key] not in allowed:
                problems.append(f"{where}: {key} must be one of {sorted(allowed)}")
        if "evidence" in f and not (isinstance(f["evidence"], list) and all(isinstance(e, str) and e for e in f["evidence"])):
            problems.append(f"{where}: evidence must be a non-empty list of strings")
        ver = f.get("verification")
        if ver is not None:
            if not isinstance(ver, dict):
                problems.append(f"{where}: verification must be an object")
            else:
                if "method" in ver and ver["method"] not in METHOD:
                    problems.append(f"{where}: verification.method must be one of {sorted(METHOD)}")
                if "verdict" in ver and ver["verdict"] not in VERDICT:
                    problems.append(f"{where}: verification.verdict must be one of {sorted(VERDICT)}")
        if f.get("severity") == "Critical":
            if "reachability" not in f:
                problems.append(f"{where}: Critical findings need reachability")
            if not (isinstance(ver, dict) and ver.get("method") == "lead"):
                problems.append(f"{where}: Critical findings need verification.method = lead")
        if "control" in f and not CONTROL_RE.match(str(f["control"])):
            problems.append(f"{where}: control must look like 8.1 or ext")
        for ref in f.get("supersedes", []) or []:
            if ref not in ids:
                problems.append(f"{where}: supersedes unknown id {ref}")
        blob = json.dumps(f)
        for rx, label in SECRET_RES:
            if rx.search(blob):
                problems.append(f"{where}: looks like it contains a {label}; cite the location, never the value")
    return problems


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    problems = check(sys.argv[1])
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        return 1
    print("findings.json is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
