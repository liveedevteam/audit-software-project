#!/usr/bin/env python3
"""Render findings.json as a self-contained findings-register.html (standard library only).

Usage: build_findings_register.py findings.json [output.html]

Findings are sorted by severity, then id. Severity counts are shown per level and never
summed into a score. Superseded and refuted findings are listed separately. The page carries an
"AI-proposed, not human-approved" label unless findings.json sets "human_approved": true at the top
level. Other scripts (audit_site.py) import render() to embed the register in a multi-page site.
"""
import html
import json
import sys

ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
CLS = {"Critical": "red", "High": "red", "Medium": "amber", "Low": "nv"}

BASE_STYLE = """<style>
:root { color-scheme: light dark; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 1150px; margin: 0 auto; padding: 0 1.5rem 3rem; line-height: 1.5; }
nav.topnav { position: sticky; top: 0; display: flex; gap: 0.4rem; padding: 0.6rem 0 0.6rem 1.5rem; margin: 0 -1.5rem 1.2rem; backdrop-filter: blur(8px); background: rgba(128,128,128,0.08); border-bottom: 1px solid rgba(128,128,128,0.25); z-index: 10; }
nav.topnav a { text-decoration: none; color: inherit; padding: 0.25rem 0.8rem; border-radius: 999px; font-size: 0.9rem; }
nav.topnav a.current { background: rgba(128,128,128,0.25); font-weight: 600; }
h1 { font-size: 1.6rem; margin: 1rem 0 0.2rem; } .meta { opacity: 0.7; font-size: 0.9rem; margin-bottom: 1.2rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.88rem; }
th, td { border: 1px solid rgba(128,128,128,0.35); padding: 0.5rem 0.6rem; text-align: left; vertical-align: top; }
th { background: rgba(128,128,128,0.12); } tr[id] { scroll-margin-top: 4rem; } tr:target { outline: 2px solid #d97706; }
.red { color: #dc2626; font-weight: 600; } .amber { color: #d97706; font-weight: 600; } .nv { color: #6b7280; font-weight: 600; }
.note { font-size: 0.85rem; opacity: 0.85; border-left: 3px solid rgba(128,128,128,0.5); padding: 0.5rem 0.9rem; margin: 0.8rem 0; }
code { background: rgba(128,128,128,0.15); padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.88em; }
</style>"""


def esc(x):
    return html.escape(str(x))


def verification_text(f):
    v = f.get("verification") or {}
    text = ", ".join(p for p in (v.get("method", ""), v.get("verdict", "")) if p)
    if v.get("note"):
        text += (": " if text else "") + v["note"]
    return text or "not reviewed"


def row(f):
    ev = "<br>".join("<code>" + esc(e) + "</code>" for e in f["evidence"])
    return (
        '<tr id="' + esc(f["id"]).lower() + '"><td>' + esc(f["id"]) + "</td><td>" + esc(f["title"]) + "</td><td>" + esc(f["domain"]) + "</td>"
        '<td class="' + CLS[f["severity"]] + '">' + esc(f["severity"]) + "</td><td>" + esc(f["effort"]) + "</td><td>" + esc(f["confidence"]) + "</td>"
        "<td>" + esc(f.get("reachability", "")) + "</td><td>" + esc(verification_text(f)) + "</td><td>" + ev + "</td><td>"
        + esc(f["recommendation"]) + "</td><td>" + esc(f.get("ticket", "")) + "</td></tr>"
    )


def split(findings):
    live = [f for f in findings if f.get("status", "open") == "open" and (f.get("verification") or {}).get("verdict") != "refuted"]
    superseded = [f for f in findings if f.get("status") == "superseded"]
    refuted = [f for f in findings if (f.get("verification") or {}).get("verdict") == "refuted"]
    live.sort(key=lambda f: (ORDER[f["severity"]], f["id"]))
    return live, superseded, refuted


def severity_strip(live):
    counts = {}
    for f in live:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    return " &middot; ".join(k + " " + str(counts[k]) for k in ("Critical", "High", "Medium", "Low") if k in counts)


def render(data, nav="", style=BASE_STYLE):
    findings = data["findings"]
    live, superseded, refuted = split(findings)
    human = bool(data.get("human_approved"))
    counts = {}
    for f in live:
        m = (f.get("verification") or {}).get("method", "none")
        counts[m] = counts.get(m, 0) + 1
    names = {"lead": "verified directly by the lead auditor", "independent-review": "reviewed by an independent agent or person",
             "self-review": "reviewed only by the same session (not independent)", "analyst": "reported by an analyst and not separately reviewed",
             "automated": "produced by an automated check", "metadata": "read from configuration or platform metadata", "none": "not reviewed"}
    breakdown = "; ".join(str(counts[k]) + " " + names[k] for k in names if k in counts)
    if human:
        label = "Findings were approved by a human reviewer."
    else:
        label = ("<strong>AI-proposed, not human-approved.</strong> Severity is a proposal. Verification breakdown: " + esc(breakdown or "none") + ". See the Verification column for each finding.")
    body = "".join(row(f) for f in live)
    extra = ""
    if superseded:
        parts = []
        for f in superseded:
            by = ", ".join(g["id"] for g in findings if f["id"] in (g.get("supersedes") or [])) or "a later finding"
            parts.append(esc(f["id"]) + " (replaced by " + esc(by) + ")")
        extra += "<h2>Superseded</h2><p>" + ", ".join(parts) + "</p>"
    if refuted:
        extra += "<h2>Refuted in review</h2><p>" + ", ".join(esc(f["id"]) + ": " + esc(f["title"]) for f in refuted) + "</p>"
    return (
        "<!-- generated -->\n<title>Findings Register — " + esc(data["project"]) + "</title>\n" + style + "\n" + nav + "\n"
        "<h1>Findings Register — " + esc(data["project"]) + "</h1>\n"
        '<div class="meta">Date: ' + esc(data["date"]) + " &middot; " + str(len(live)) + " findings &middot; counts per severity (not a score): " + severity_strip(live) + "</div>\n"
        '<p class="note">' + label + "</p>\n"
        "<table><thead><tr><th>ID</th><th>Title</th><th>Domain</th><th>Severity</th><th>Effort</th><th>Confidence</th><th>Reachable by</th><th>Verification</th><th>Evidence (locations only)</th><th>Recommendation</th><th>Ticket</th></tr></thead><tbody>\n"
        + body + "</tbody></table>\n" + extra +
        '\n<p class="note">Remediation chain: finding, recommendation, remediation task, ticket, developer, pull request. Tickets are drafted only after the requester approves them.</p>\n'
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    data = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "findings-register.html"
    open(out, "w").write(render(data))
    print("wrote " + out + " (" + str(len(split(data["findings"])[0])) + " findings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
