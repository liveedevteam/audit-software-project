#!/usr/bin/env python3
"""Build the full-mode audit site from three JSON files (standard library only).

Usage:
  audit_site.py --findings findings.json --context system-context.json --audit audit.json --out <dir>

Writes three self-contained pages into <dir>:
  index.html            platform overview (description, domains, C4 level 1 and 2, stack, environments,
                        deployment flow, critical flows, access model) plus the audit dashboard
  audit-report.html     executive summary, blockers, plan, findings by area, questions, boundary
  findings-register.html  the findings register

Data files: see references/findings-schema.md, references/system-context-schema.md and
references/audit-json-schema.md. Nothing project-specific is embedded in this script. Findings shown as red
tags on the diagrams come from each component's "finding_ids".
"""
import argparse
import html
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_findings_register as reg  # noqa: E402
import validate_findings  # noqa: E402

SEV_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def esc(x):
    return html.escape(str(x))


# ---------------------------------------------------------------- data helpers
class Findings:
    def __init__(self, data):
        self.data = data
        self.by_id = {f["id"]: f for f in data["findings"]}

    def worst(self, ids):
        sevs = [self.by_id[i]["severity"] for i in ids if i in self.by_id]
        return min(sevs, key=lambda s: SEV_RANK[s]) if sevs else None

    def pills(self, ids):
        out = ""
        for i in ids:
            f = self.by_id.get(i)
            cls = "r" if f and f["severity"] in ("Critical", "High") else "a"
            out += '<a class="pill ' + cls + '" href="findings-register.html#' + esc(i).lower() + '">' + esc(i) + "</a>"
        return out


def check_refs(ctx, audit, F):
    problems = []
    def need(ids, where):
        for i in ids or []:
            if i not in F.by_id:
                problems.append(where + ": unknown finding id " + i)
    need(ctx.get("system", {}).get("finding_ids"), "system")
    for key in ("actors", "externals", "containers", "domains", "deployment_steps", "flows"):
        for item in ctx.get(key, []):
            need(item.get("finding_ids"), key + " " + str(item.get("id") or item.get("name")))
    need(audit.get("blockers"), "audit.blockers")
    for p in audit.get("plan", []):
        need(p.get("finding_ids"), "audit.plan")
    ids = {c["id"] for c in ctx.get("containers", [])}
    for e in ctx.get("container_edges", []):
        for end in ("from", "to"):
            if e[end] not in ids and e[end] not in {x["id"] for x in ctx.get("externals", [])}:
                problems.append("container_edges: unknown component " + e[end])
    return problems


# ---------------------------------------------------------------- SVG helpers
class Svg:
    def __init__(self, w):
        self.w, self.h, self.p = w, 0, []

    def grow(self, y):
        self.h = max(self.h, y)

    def box(self, x, y, w, h, title, lines=(), kind="bx", tags=None):
        self.p.append('<rect class="%s" x="%s" y="%s" width="%s" height="%s" rx="8"/>' % (kind, x, y, w, h))
        ty = y + 20
        self.p.append('<text class="t" x="%s" y="%s" text-anchor="middle">%s</text>' % (x + w / 2, ty, esc(title)))
        for i, line in enumerate(lines):
            self.p.append('<text class="s" x="%s" y="%s" text-anchor="middle">%s</text>' % (x + w / 2, ty + 15 + i * 13, esc(line)))
        if tags:
            self.tag(x + w - 4, y - 2, tags[0], tags[1])
        self.grow(y + h)

    def tag(self, x, y, label, sev):
        wd = 7 * len(label) + 10
        cls = "fd" if sev in ("Critical", "High") else "fa"
        self.p.append('<rect class="%s" x="%s" y="%s" width="%s" height="16" rx="8"/><text class="ft" x="%s" y="%s" text-anchor="middle">%s</text>'
                      % (cls, x - wd, y - 9, wd, x - wd / 2, y + 3, esc(label)))

    def line(self, x1, y1, x2, y2, label=None, lx=None, ly=None, dashed=False, both=False):
        cls = "ln dash" if dashed else "ln"
        ms = ' marker-start="url(#ah2)"' if both else ""
        self.p.append('<line class="%s" x1="%s" y1="%s" x2="%s" y2="%s" marker-end="url(#ah)"%s/>' % (cls, x1, y1, x2, y2, ms))
        if label:
            lx = (x1 + x2) / 2 if lx is None else lx
            ly = (y1 + y2) / 2 - 4 if ly is None else ly
            self.p.append('<text class="s l" x="%s" y="%s" text-anchor="middle">%s</text>' % (lx, ly, esc(label)))

    def text(self, x, y, s, cls="s", anchor="start"):
        self.p.append('<text class="%s" x="%s" y="%s" text-anchor="%s">%s</text>' % (cls, x, y, anchor, esc(s)))
        self.grow(y + 6)

    def raw(self, s):
        self.p.append(s)

    def render(self, ident, desc):
        defs = ('<defs><marker id="ah-%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="ar"/></marker>'
                '<marker id="ah2-%s" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M10 0L0 5L10 10z" class="ar"/></marker></defs>') % (ident, ident)
        body = "".join(self.p).replace("url(#ah)", "url(#ah-%s)" % ident).replace("url(#ah2)", "url(#ah2-%s)" % ident)
        return ('<svg id="%s" viewBox="0 0 %s %s" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (ident, self.w, self.h + 10, esc(desc))
                + defs + body + "</svg>")


def tags_for(F, ids):
    ids = [i for i in (ids or []) if i in F.by_id]
    if not ids:
        return None
    label = " / ".join(i for i in ids[:2]) + (" +%d" % (len(ids) - 2) if len(ids) > 2 else "")
    return (label, F.worst(ids))


def box_height(lines):
    return 30 + 15 + 13 * max(len(lines), 1) - 13 + 10


def edge_point(b, tx, ty):
    x, y, w, h = b
    cx, cy = x + w / 2, y + h / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def c4_context(ctx, F):
    s = Svg(940)
    actors = ctx.get("actors", [])
    n = max(len(actors), 1)
    aw = min(270, (880 - (n - 1) * 30) / n)
    x0 = (940 - (aw * n + 30 * (n - 1))) / 2
    s.text(470, 24, "Actors", "h", "middle")
    sysd = ctx["system"]
    sys_x, sys_w = 250, 440
    sys_y = 215
    sys_lines = sysd.get("lines", [])
    sys_h = max(110, box_height(sys_lines) + 20)
    edge_labels = {e["from"]: e.get("label", "uses") for e in ctx.get("actor_edges", [])}
    for i, a in enumerate(actors):
        x = x0 + i * (aw + 30)
        lines = a.get("lines", [])
        s.box(x, 40, aw, 78, a["name"], lines, "pr", tags_for(F, a.get("finding_ids")))
        tx = min(max(x + aw / 2, sys_x + 40), sys_x + sys_w - 40)
        s.line(x + aw / 2, 118, tx, sys_y, edge_labels.get(a["id"], "uses"), (x + aw / 2 + tx) / 2, 165)
    s.box(sys_x, sys_y, sys_w, sys_h, sysd["name"], sys_lines, "sy", tags_for(F, sysd.get("finding_ids")))
    ext = ctx.get("externals", [])
    per_row = 6
    y = sys_y + sys_h + 60
    s.text(30, y - 17, "External systems", "h")
    for r in range(0, len(ext), per_row):
        row_items = ext[r:r + per_row]
        k = len(row_items)
        bw = min(140, (940 - 60 - (k - 1) * 20) / k)
        rx0 = (940 - (bw * k + 20 * (k - 1))) / 2
        for j, e in enumerate(row_items):
            x = rx0 + j * (bw + 20)
            s.box(x, y, bw, 62, e["name"], [e.get("note", "")], "ex", tags_for(F, e.get("finding_ids")))
            if r == 0:
                sx = min(max(x + bw / 2, sys_x + 40), sys_x + sys_w - 40)
                s.line(sx, sys_y + sys_h, x + bw / 2, y, None, dashed=True, both=True)
        y += 90
    s.text(30, y + 10, "Red tags mark audit findings on that element (amber for Medium or Low). See the Findings page.", "s")
    return s.render("c4-l1", "C4 level 1 system context diagram")


def c4_containers(ctx, F):
    s = Svg(1000)
    conts = ctx.get("containers", [])
    clients = [c for c in conts if c.get("placement") == "client"]
    outside = [c for c in conts if c.get("placement") == "outside"]
    inside = [c for c in conts if c.get("placement", "inside") == "inside"]
    geo = {}
    placement = {c["id"]: c.get("placement", "inside") for c in conts}
    y = 60
    for c in clients:
        h = box_height(c.get("lines", []))
        geo[c["id"]] = (20, y, 200, h)
        y += h + 40
    left_bottom = y
    tiers = {}
    for c in inside:
        tiers.setdefault(int(c.get("tier", 0)), []).append(c)
    by = 70
    for t in sorted(tiers):
        row_items = tiers[t]
        k = len(row_items)
        bw = min(190, (500 - (k - 1) * 20) / k)
        rx0 = 260 + (500 - (bw * k + 20 * (k - 1))) / 2
        rh = max(box_height(c.get("lines", [])) for c in row_items)
        for j, c in enumerate(row_items):
            geo[c["id"]] = (rx0 + j * (bw + 20), by, bw, box_height(c.get("lines", [])))
        by += rh + 70
    boundary_bottom = by - 10
    oy = max(left_bottom, 340)
    for c in outside:
        h = box_height(c.get("lines", []))
        geo[c["id"]] = (20, oy, 200, h)
        oy += h + 40
    ext = ctx.get("externals", [])
    ey = 55
    for e in ext:
        geo["ext:" + e["id"]] = (800, ey, 190, 56)
        ey += 68
    if clients:
        s.text(20, 40, ctx.get("client_label", "Users reach the client over HTTPS"), "s")
    s.raw('<rect class="bd" x="250" y="30" width="520" height="%s" rx="12"/>' % (boundary_bottom - 30))
    s.grow(boundary_bottom)
    s.text(265, boundary_bottom - 8, ctx.get("boundary_label", "Runtime boundary"), "h")
    for c in conts:
        x, y0, w, h = geo[c["id"]]
        s.box(x, y0, w, h, c["name"], c.get("lines", []), "bx", tags_for(F, c.get("finding_ids")))
    for e in ctx.get("container_edges", []):
        a, b = geo.get(e["from"]), geo.get(e["to"])
        if not a or not b:
            continue
        if placement.get(e["from"]) == "outside":
            # components outside the boundary (CI/CD, observability) point at the boundary edge, so the
            # arrow never cuts across boxes inside it
            p1 = (a[0] + a[2], a[1] + a[3] / 2)
            p2 = (250, min(max(p1[1], 60), boundary_bottom - 25))
        else:
            p1 = edge_point(a, b[0] + b[2] / 2, b[1] + b[3] / 2)
            p2 = edge_point(b, a[0] + a[2] / 2, a[1] + a[3] / 2)
        s.line(p1[0], p1[1], p2[0], p2[1], e.get("label"), (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 - 5, dashed=bool(e.get("dashed")))
    if ext:
        s.text(800, 40, "External systems", "h")
        caller = geo.get(ctx.get("external_caller", ""))
        last_y = geo["ext:" + ext[-1]["id"]][1] + 28
        if caller:
            cx, cy = caller[0] + caller[2] / 2, caller[1]
            if abs(cy - 70) < 5:
                s.raw('<polyline class="ln dash" fill="none" points="%s,%s %s,48 790,48 790,%s"/>' % (cx, cy, cx, last_y))
            else:
                s.raw('<polyline class="ln dash" fill="none" points="%s,%s 790,%s 790,%s"/>' % (caller[0] + caller[2], caller[1] + caller[3] / 2, caller[1] + caller[3] / 2, last_y))
        for e in ext:
            gx, gy, gw, gh = geo["ext:" + e["id"]]
            s.box(gx, gy, gw, gh, e["name"], [e.get("note", "")], "ex", tags_for(F, e.get("finding_ids")))
            s.line(790, gy + 28, 800, gy + 28)
    ly = s.h + 30
    s.text(20, ly, "Solid arrows: internal calls. Dashed: calls to external systems. Red tags mark audit findings (amber for Medium or Low).", "s")
    return s.render("c4-l2", "C4 level 2 container diagram")


def deployment_flow(ctx, F):
    steps = ctx.get("deployment_steps", [])
    if not steps:
        return ""
    s = Svg(1000)
    n = len(steps)
    w = min(150, (960 - (n - 1) * 22) / n)
    x0 = (1000 - (w * n + 22 * (n - 1))) / 2
    if ctx.get("deployment_note"):
        s.text(20, 24, ctx["deployment_note"], "s")
    h = max(box_height(st.get("lines", [])) for st in steps)
    for i, st in enumerate(steps):
        x = x0 + i * (w + 22)
        s.box(x, 50, w, h, st["name"], st.get("lines", []), "bx", tags_for(F, st.get("finding_ids")))
        if i:
            s.line(x - 22, 50 + h / 2, x, 50 + h / 2)
    s.text(20, 50 + h + 30, "Red tags: audit findings attached to that step.", "s")
    return s.render("deploy-flow", "Deployment flow")


# ---------------------------------------------------------------- page pieces
CSS = """<style>
:root { color-scheme: light dark; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 1040px; margin: 0 auto; padding: 0 1.5rem 3rem; line-height: 1.5; }
nav.topnav { position: sticky; top: 0; display: flex; gap: 0.4rem; padding: 0.6rem 0 0.6rem 1.5rem; margin: 0 -1.5rem 1.2rem; backdrop-filter: blur(8px); background: rgba(128,128,128,0.08); border-bottom: 1px solid rgba(128,128,128,0.25); z-index: 10; }
nav.topnav a { text-decoration: none; color: inherit; padding: 0.25rem 0.8rem; border-radius: 999px; font-size: 0.9rem; }
nav.topnav a.current { background: rgba(128,128,128,0.25); font-weight: 600; }
nav.topnav a:hover:not(.current) { background: rgba(128,128,128,0.15); }
h1 { font-size: 1.6rem; margin: 1rem 0 0.2rem; } h2 { font-size: 1.15rem; margin-top: 2rem; border-bottom: 1px solid rgba(128,128,128,0.4); padding-bottom: 0.25rem; scroll-margin-top: 4rem; }
h3 { font-size: 1rem; margin: 1.2rem 0 0.3rem; }
.meta { opacity: 0.7; font-size: 0.9rem; margin-bottom: 1.2rem; } .lead { font-size: 1.02rem; margin: 0.4rem 0 1rem; } .note { font-size: 0.85rem; opacity: 0.8; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.6rem; margin: 1rem 0 1.4rem; }
.stat { border: 1px solid rgba(128,128,128,0.35); border-radius: 8px; padding: 0.6rem 0.8rem; } .stat b { display: block; font-size: 1.25rem; } .stat span { font-size: 0.8rem; opacity: 0.75; }
.toc { font-size: 0.85rem; display: flex; flex-wrap: wrap; gap: 0.3rem 0.9rem; padding: 0.5rem 0.9rem; border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; margin: 0.6rem 0 1.2rem; } .toc a { color: inherit; text-decoration: none; opacity: 0.85; }
table.t { border-collapse: collapse; width: 100%; margin: 0.6rem 0; font-size: 0.87rem; } table.t th, table.t td { border: 1px solid rgba(128,128,128,0.35); padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; } table.t th { background: rgba(128,128,128,0.12); }
figure { margin: 1rem 0; } figure svg { width: 100%; height: auto; border: 1px solid rgba(128,128,128,0.3); border-radius: 8px; padding: 0.4rem; box-sizing: border-box; } figcaption { font-size: 0.85rem; opacity: 0.8; margin-top: 0.3rem; }
svg text { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; } svg .t { font-size: 13px; font-weight: 600; } svg .s { font-size: 11px; opacity: 0.8; } svg .h { font-size: 12px; font-weight: 600; opacity: 0.85; } svg .l { font-size: 10.5px; opacity: 0.7; }
svg .bx { fill: rgba(128,128,128,0.10); stroke: currentColor; stroke-opacity: 0.55; stroke-width: 1.2; } svg .pr { fill: rgba(22,163,74,0.12); stroke: #16a34a; stroke-width: 1.3; } svg .sy { fill: rgba(37,99,235,0.14); stroke: #2563eb; stroke-width: 1.6; }
svg .ex { fill: rgba(128,128,128,0.06); stroke: currentColor; stroke-opacity: 0.5; stroke-width: 1.2; stroke-dasharray: 5 3; } svg .bd { fill: none; stroke: currentColor; stroke-opacity: 0.35; stroke-width: 1.2; stroke-dasharray: 8 4; }
svg .ln { stroke: currentColor; stroke-opacity: 0.6; stroke-width: 1.3; fill: none; } svg .ln.dash { stroke-dasharray: 4 3; stroke-opacity: 0.4; } svg .ar { fill: currentColor; fill-opacity: 0.65; }
svg .fd { fill: #dc2626; } svg .fa { fill: #d97706; } svg .ft { fill: #fff; font-size: 10px; font-weight: 600; }
.pill { display: inline-block; font-size: 0.75rem; border: 1px solid rgba(128,128,128,0.4); border-radius: 999px; padding: 0.02rem 0.5rem; margin: 0.1rem 0.15rem 0.1rem 0; text-decoration: none; color: inherit; }
.pill.r { border-color: rgba(220,38,38,0.5); background: rgba(220,38,38,0.08); } .pill.a { border-color: rgba(217,119,6,0.5); background: rgba(217,119,6,0.08); }
.callout { border-left: 4px solid #d97706; padding: 0.7rem 1rem; background: rgba(217,119,6,0.08); margin: 1rem 0; border-radius: 0 8px 8px 0; }
.chips { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0 1.2rem; } .chip { border-radius: 999px; padding: 0.3rem 0.9rem; font-size: 0.88rem; font-weight: 600; border: 1px solid rgba(128,128,128,0.35); }
.chip.red { background: rgba(220,38,38,0.1); border-color: rgba(220,38,38,0.4); } .chip.amber { background: rgba(217,119,6,0.1); border-color: rgba(217,119,6,0.3); } .chip.nv { background: rgba(107,114,128,0.12); }
.blockers { border-left: 4px solid #dc2626; padding: 0.8rem 1rem; background: rgba(220,38,38,0.08); border-radius: 0 8px 8px 0; } .blockers a, ul.todo a { color: inherit; }
.blockers-none { border-left: 4px solid #16a34a; padding: 0.8rem 1rem; background: rgba(22,163,74,0.08); border-radius: 0 8px 8px 0; }
ul.todo { list-style: none; padding: 0; margin: 0.8rem 0; } ul.todo li { display: flex; gap: 0.7rem; align-items: flex-start; padding: 0.7rem 0.9rem; border: 1px solid rgba(128,128,128,0.3); border-radius: 8px; margin-bottom: 0.6rem; }
ul.todo input[type=checkbox] { margin-top: 0.3rem; width: 1.05rem; height: 1.05rem; accent-color: #16a34a; cursor: pointer; flex-shrink: 0; } ul.todo li.done { opacity: 0.55; } ul.todo li.done .txt { text-decoration: line-through; }
.cards { margin-top: 1.4rem; } .card { display: block; border: 1px solid rgba(128,128,128,0.35); border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 0.8rem; text-decoration: none; color: inherit; } .card:hover { background: rgba(128,128,128,0.08); } .card h3 { margin: 0 0 0.25rem; } .card p { margin: 0; opacity: 0.75; font-size: 0.88rem; }
.finding { border: 1px solid rgba(128,128,128,0.3); border-radius: 8px; padding: 0.8rem 1rem; margin: 0.8rem 0; } .finding h4 { margin: 0 0 0.4rem; font-size: 0.98rem; } .finding p { margin: 0.25rem 0; font-size: 0.9rem; }
.red { color: #dc2626; font-weight: 600; } .amber { color: #d97706; font-weight: 600; } .nv { color: #6b7280; font-weight: 600; }
code { background: rgba(128,128,128,0.15); padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.88em; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.88rem; } th, td { border: 1px solid rgba(128,128,128,0.35); padding: 0.5rem 0.6rem; text-align: left; vertical-align: top; } th { background: rgba(128,128,128,0.12); }
tr[id] { scroll-margin-top: 4rem; } tr:target { outline: 2px solid #d97706; }
</style>"""


def nav(cur):
    items = [("index", "Overview"), ("audit-report", "Audit Report"), ("findings-register", "Findings")]
    return '<nav class="topnav">' + "".join(
        '<a%s href="%s.html">%s</a>' % (' class="current"' if cur == f else "", f, l) for f, l in items) + "</nav>"


def rows(rs):
    return "".join("<tr>" + "".join("<td>" + c + "</td>" for c in r) + "</tr>" for r in rs)


def severity_chips(F):
    live, _, _ = reg.split(F.data["findings"])
    counts = {}
    for f in live:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    cls = {"Critical": "red", "High": "red", "Medium": "amber", "Low": "nv"}
    return '<div class="chips">' + "".join(
        '<a class="chip %s" href="findings-register.html" style="text-decoration:none;color:inherit">%d %s</a>' % (cls[k], counts[k], k)
        for k in ("Critical", "High", "Medium", "Low") if k in counts) + "</div>"


def dashboard(audit, F, slug):
    blockers = audit.get("blockers", [])
    if blockers:
        b = '<div class="blockers">' + "<br>".join(
            '<a href="findings-register.html#%s">%s</a>: %s' % (esc(i).lower(), esc(i), esc(F.by_id[i]["title"])) for i in blockers) + "</div>"
    else:
        b = '<div class="blockers-none">No immediate blockers identified.</div>'
    plan = "".join(
        '<li><input type="checkbox" data-k="a%d"><span class="txt"><strong>%s:</strong> %s %s</span></li>' % (n, esc(p["area"]), esc(p["action"]), F.pills(p.get("finding_ids", [])))
        for n, p in enumerate(audit.get("plan", [])[:5], 1))
    js = """<script>
(function () {
  var KEY = "audit-%s";
  var saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
  document.querySelectorAll("#todo input[type=checkbox]").forEach(function (cb) {
    var k = cb.getAttribute("data-k");
    if (saved[k]) { cb.checked = true; cb.closest("li").classList.add("done"); }
    cb.addEventListener("change", function () {
      saved[k] = cb.checked;
      cb.closest("li").classList.toggle("done", cb.checked);
      try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {}
    });
  });
})();
</script>""" % slug
    return (severity_chips(F) + "<h3>Do these first</h3>" + b + "<h3>30-day plan (at most five actions)</h3>"
            '<ul class="todo" id="todo">' + plan + "</ul>" + js)


def overview_page(ctx, audit, F, slug):
    d = ctx
    toc = "".join('<a href="#%s">%s</a>' % (a, l) for a, l in [
        ("glance", "At a glance"), ("domains", "Domains"), ("c4l1", "C4 level 1"), ("c4l2", "C4 level 2"), ("stack", "Stack &amp; environments"),
        ("deploy", "Deployment"), ("flows", "Critical flows"), ("access", "Access model"), ("audit", "Audit summary")])
    stats = "".join('<div class="stat"><b>%s</b><span>%s</span></div>' % (esc(s["value"]), esc(s["label"])) for s in d.get("stats", []))
    dom = rows([[esc(x["name"]), esc(x["covers"]), esc(x.get("modules", "")), F.pills(x.get("finding_ids", []))] for x in d.get("domains", [])])
    stack = rows([[esc(x["layer"]), esc(x["tech"])] for x in d.get("stack", [])])
    envs = rows([[esc(x["name"]), esc(x.get("detail", "")), esc(x.get("notes", ""))] for x in d.get("environments", [])])
    flows = rows([[esc(x["name"]), esc(x["what"]), esc(x.get("status", "")), F.pills(x.get("finding_ids", []))] for x in d.get("flows", [])])
    unconfirmed = ""
    if d.get("unconfirmed"):
        unconfirmed = '<p class="note">Not confirmed: ' + esc("; ".join(d["unconfirmed"])) + ".</p>"
    timing = '<div class="callout"><strong>Timing:</strong> ' + esc(d["timing_note"]) + "</div>" if d.get("timing_note") else ""
    flow_svg = deployment_flow(d, F)
    return (
        "<!-- generated -->\n<title>Overview — " + esc(d["project"]) + "</title>\n" + CSS + "\n" + nav("index") + "\n"
        "<h1>" + esc(d["project"]) + '</h1>\n<div class="meta">Platform overview and audit summary &middot; ' + esc(audit["date"]) + "</div>\n"
        '<p class="lead">' + esc(d["description"]) + "</p>\n" + timing +
        '<div class="toc">' + toc + "</div>\n"
        '<h2 id="glance">At a glance</h2><div class="stats">' + stats + "</div>\n"
        '<h2 id="domains">Domains</h2><p class="note">Pills show audit findings in that area (red = High or Critical, amber = Medium or Low).</p>'
        '<table class="t"><thead><tr><th>Domain</th><th>What it covers</th><th>Main modules</th><th>Findings</th></tr></thead><tbody>' + dom + "</tbody></table>\n"
        '<h2 id="c4l1">C4 level 1: system context</h2><figure>' + c4_context(d, F) + "<figcaption>Who uses the platform and which external systems it depends on.</figcaption></figure>\n"
        '<h2 id="c4l2">C4 level 2: containers</h2><figure>' + c4_containers(d, F) + "<figcaption>Runtime building blocks and how they connect." + (" " + esc(d.get("container_caption", "")) if d.get("container_caption") else "") + "</figcaption></figure>" + unconfirmed + "\n"
        '<h2 id="stack">Technology stack and environments</h2><table class="t"><thead><tr><th>Layer</th><th>Technology</th></tr></thead><tbody>' + stack + "</tbody></table>"
        '<table class="t"><thead><tr><th>Environment</th><th>Detail</th><th>Notes</th></tr></thead><tbody>' + envs + "</tbody></table>\n"
        + ('<h2 id="deploy">Deployment flow</h2><figure>' + flow_svg + "</figure>\n" if flow_svg else '<h2 id="deploy">Deployment flow</h2><p class="note">Not provided.</p>\n') +
        '<h2 id="flows">Critical business flows</h2><table class="t"><thead><tr><th>Flow</th><th>What happens</th><th>Audit validation</th><th>Findings</th></tr></thead><tbody>' + flows + "</tbody></table>\n"
        '<h2 id="access">Access model</h2><p>' + esc(d.get("access_model", "Not provided.")) + "</p>\n"
        '<h2 id="audit">Audit summary</h2><p class="note">All findings are AI-proposed unless the register says a human approved them.</p>' + dashboard(audit, F, slug) +
        '\n<div class="cards"><a class="card" href="audit-report.html"><h3>Audit Report →</h3><p>Executive summary, findings by area, questions, inspection boundary.</p></a>'
        '<a class="card" href="findings-register.html"><h3>Findings Register →</h3><p>Every finding with severity, effort and verification status.</p></a></div>\n'
    )


def report_page(audit, F):
    live, _, _ = reg.split(F.data["findings"])
    areas = {}
    for f in live:
        areas.setdefault(f["domain"].split(" / ")[0], []).append(f)
    cls = {"Critical": "red", "High": "red", "Medium": "amber", "Low": "nv"}
    sections = ""
    for area in sorted(areas, key=lambda a: min(SEV_RANK[f["severity"]] for f in areas[a])):
        sections += '<h3 id="a-%s">%s</h3>' % (re.sub(r"[^a-z0-9]+", "-", area.lower()), esc(area))
        for f in areas[area]:
            ev = ", ".join("<code>" + esc(e) + "</code>" for e in f["evidence"])
            sections += (
                '<div class="finding" id="%s"><h4><span class="%s">%s</span> %s: %s</h4>'
                "<p><strong>Observation:</strong> %s</p><p><strong>Impact:</strong> %s</p><p><strong>Recommendation:</strong> %s</p>"
                "<p><strong>Evidence:</strong> %s</p><p class=\"note\">Effort %s &middot; %s &middot; %s &middot; verification: %s</p></div>"
                % (esc(f["id"]).lower(), cls[f["severity"]], esc(f["severity"]), esc(f["id"]), esc(f["title"]), esc(f["observation"]), esc(f["impact"]),
                   esc(f["recommendation"]), ev, esc(f["effort"]), esc(f["confidence"]), esc(f.get("reachability", "reach n/a")), esc(reg.verification_text(f))))
    summary = "".join("<p>" + esc(p) + "</p>" for p in audit.get("summary", []))
    blockers = ("<ul>" + "".join('<li><a href="#%s">%s</a>: %s</li>' % (esc(i).lower(), esc(i), esc(F.by_id[i]["title"])) for i in audit.get("blockers", [])) + "</ul>") if audit.get("blockers") else "<p>None identified.</p>"
    plan = "<ol>" + "".join("<li><strong>%s:</strong> %s %s</li>" % (esc(p["area"]), esc(p["action"]), F.pills(p.get("finding_ids", []))) for p in audit.get("plan", [])[:5]) + "</ol>"
    questions = "<ul>" + "".join("<li>%s <em>(%s)</em></li>" % (esc(q["question"]), esc(q.get("area", ""))) for q in audit.get("questions", [])) + "</ul>"
    b = audit.get("boundary", {})
    nr = "<p>Not reached this pass: " + esc("; ".join(audit["not_reached"])) + ".</p>" if audit.get("not_reached") else ""
    return (
        "<!-- generated -->\n<title>Audit Report — " + esc(audit["project"]) + "</title>\n" + CSS + "\n" + nav("audit-report") + "\n"
        "<h1>Audit Report — " + esc(audit["project"]) + '</h1><div class="meta">Date: ' + esc(audit["date"]) + " &middot; Auditor: " + esc(audit.get("auditor", "AI-assisted audit")) + "</div>\n"
        '<p class="note">Findings marked Suspected, or with a verification note, can be revised if the owner holds evidence this audit could not access. See the questions below. Severity is AI-proposed unless the register says a human approved it.</p>\n'
        "<h2>Executive summary</h2>" + summary + "<h2>Immediate blockers</h2>" + blockers + "<h2>30-day improvement plan</h2>" + plan +
        "<h2>Risk context</h2><p>" + esc(audit.get("risk_context", "")) + "</p>\n<h2>Findings by area</h2>" + sections + nr +
        "<h2>Questions requiring human confirmation</h2>" + questions +
        "<h2>Inspection boundary</h2><p><strong>Checked:</strong> " + esc(b.get("checked", "")) + "</p><p><strong>Not checked:</strong> " + esc(b.get("not_checked", "")) + "</p>"
        "<p><strong>Tools run:</strong> " + esc(b.get("tools", "")) + "</p>"
        "<p>Accessibility and internationalization were not assessed; they require browser-based testing outside this audit's static-analysis scope.</p>\n"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--findings", required=True)
    ap.add_argument("--context", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bad = validate_findings.check(a.findings)
    if bad:
        print("findings.json is not valid; run scripts/validate_findings.py for details:")
        for p in bad:
            print(" -", p)
        return 1
    findings = json.load(open(a.findings))
    ctx = json.load(open(a.context))
    audit = json.load(open(a.audit))
    F = Findings(findings)
    problems = check_refs(ctx, audit, F)
    if problems:
        print("Input problems:")
        for p in problems:
            print(" -", p)
        return 1
    os.makedirs(a.out, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", audit["project"].lower()).strip("-") + "-" + audit["date"]
    open(os.path.join(a.out, "index.html"), "w").write(overview_page(ctx, audit, F, slug))
    open(os.path.join(a.out, "audit-report.html"), "w").write(report_page(audit, F))
    open(os.path.join(a.out, "findings-register.html"), "w").write(reg.render(findings, nav("findings-register"), CSS))
    print("wrote index.html, audit-report.html, findings-register.html to " + a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
