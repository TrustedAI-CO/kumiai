#!/usr/bin/env python3
"""Test-traceability tool — one file, four commands. No LLM, no dataset.

    python trace.py audit        # integrity: every link resolves, or exit non-zero (CI gate)
    python trace.py report       # terminal: project stats + per-feature table
    python trace.py json         # write docs/trace.json — the computed model (single artifact)
    python trace.py dashboard    # write docs/dashboard.html + spec-*.html (renderers over the model)

Reads the standard docs (see FRAMEWORK-MANUAL.md), all plain markdown + tags:
    docs/functions.md   | id | name | module | intent | importance | scope |
    docs/intent.md          ## Goals   | G1 | … |
    docs/architecture.md    ## Modules | retrieve | … |
    docs/specs/*.md         frontmatter feature: + Behavior rows | R1 | … |
    tests/**/*.py           # spec: SPEC-<id> R<n>     (top-down: test proves a rule)
    src/**/*.py             # feature: <id>            (bottom-up: file implements a feature)

State per feature: spec + every Rn tagged = covered; spec + a bare Rn = spec-only;
no spec = untraced; scope: deferred = out of scope (reported, not scored). A spec is
flagged stale when an implementing file was committed after it (git mtimes).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SPECS = DOCS / "specs"
TEST_GLOBS = ["tests/**/*.py", "**/tests/**/*.py", "**/*.test.ts", "**/*.spec.ts", "**/*.test.js"]
SRC_GLOBS = ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.go", "**/*.rs"]
PRUNE = ("/.git/", "/node_modules/", "/.venv/", "/venv/", "/dist/", "/build/",
         "/__pycache__/", "/.next/", "/docs/")

FM = re.compile(r"^---\n(.*?)\n---", re.S)
ROW = re.compile(r"^\|\s*(R\d+)\s*\|", re.M)
ROWFULL = re.compile(r"^\|\s*(R\d+)\s*\|(.+)$", re.M)  # R-id + remaining cells
SPEC_TAG = re.compile(r"(?:#|//)\s*spec:\s*(SPEC-[\w-]+)\s+(R\d+)")  # test → rule (# or //)
FEATURE_TAG = re.compile(r"(?:#|//)\s*feature:\s*([\w-]+)")  # bottom-up: source → feature
# functions row: | id | name | module | intent | importance | scope |
FROW = re.compile(
    r"^\|[ \t]*([\w-]+)[ \t]*\|[ \t]*(.+?)[ \t]*\|[ \t]*(.+?)[ \t]*\|[ \t]*(.+?)[ \t]*\|"
    r"[ \t]*(must|should|could)[ \t]*\|[ \t]*(active|deferred)[ \t]*\|",
    re.M,
)
GOAL = re.compile(r"^\|\s*(G\d+)\s*\|", re.M)
MODULE = re.compile(r"^\|\s*([\w./-]+)\s*\|\s*.+?\s*\|", re.M)

WEIGHT = {"must": 2.0, "should": 1.0, "could": 0.5}
STATE_LABEL = {"green": "covered", "red": "spec-only", "gray": "untraced"}


# ── parsing ─────────────────────────────────────────────────────────────
def _field(fm: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return re.sub(r"\s+#.*$", "", m.group(1)).strip() if m else ""


def project_name() -> str:
    """Human name for this project — `project:` in intent.md frontmatter if set, else the
    git repo / root directory name. Keeps each dashboard's tab title distinct."""
    f = DOCS / "intent.md"
    if f.exists():
        m = FM.search(f.read_text())
        if m:
            p = _field(m.group(1), "project")
            if p:
                return p
    return ROOT.name


def load_features() -> list[dict]:
    text = (DOCS / "functions.md").read_text()
    return [
        {"id": m[0], "name": m[1], "module": m[2], "intent": m[3],
         "importance": m[4], "scope": m[5]}
        for m in FROW.findall(text)
    ]


def load_goals() -> set:
    f = DOCS / "intent.md"
    return set(GOAL.findall(f.read_text())) if f.exists() else set()


def load_modules() -> dict:
    """module -> [depends-on modules]. Reads the `## Modules` table; the optional 3rd
    column is a comma/slash list of upstream modules (a DAG). Empty / — = no deps."""
    f = DOCS / "architecture.md"
    if not f.exists():
        return {}
    text = f.read_text()
    m = re.search(r"^## Modules\b(.*?)(?=^## |\Z)", text, re.S | re.M)
    section = m.group(1) if m else ""
    out: dict[str, list] = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        name = cells[0]
        if name.lower() in ("module", "id", "node", "") or set(name) <= set("-: "):
            continue
        deps = []
        if len(cells) >= 3 and cells[2] not in ("", "—", "-"):
            deps = [d for d in (x.strip() for x in re.split(r"[,/]", cells[2])) if d and d != "—"]
        out[name] = deps
    return out


def load_specs() -> dict:
    out = {}
    for f in SPECS.glob("*.md"):
        if f.name.startswith("_") or "template" in f.name:
            continue
        m = FM.search(f.read_text())
        if not m:
            continue
        sid = _field(m.group(1), "id")
        if sid:
            text = f.read_text()
            detail = {rid: [c.strip() for c in cells.rstrip("|").split("|")]
                      for rid, cells in ROWFULL.findall(text)}
            out[sid] = {"feature": _field(m.group(1), "feature"),
                        "status": _field(m.group(1), "status") or "draft",
                        "rows": ROW.findall(text), "detail": detail,
                        "file": f.relative_to(ROOT).as_posix()}
    return out


def _ignored_dirs() -> set:
    """Git-ignored directory paths — vendored trees we must never scan.

    A glob like `**/tests/**/*.py` will happily walk a 40k-file vendored checkout that
    git already knows to ignore, which is both slow and a source of decode/IsADirectory
    crashes. Ask git once instead of maintaining PRUNE by hand.

    These are FULL relative paths, not top-level names. Keeping only the first path
    segment silently pruned the whole repo: `backend/.venv/` and
    `frontend/node_modules/` are ignored, and their first segments are `backend` and
    `frontend` — the entire source tree. Every feature then reported `gap 0/N` because
    no `# feature:`/`# spec:` tag was ever scanned, while `audit` still exited 0.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--others", "--ignored",
             "--exclude-standard", "--directory"],
            capture_output=True, text=True, timeout=30,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line.rstrip("/") for line in out.splitlines() if line.strip()}


_IGNORED = None


def _pruned(f: Path) -> bool:
    global _IGNORED
    if _IGNORED is None:
        _IGNORED = _ignored_dirs()
    rel = f.relative_to(ROOT).as_posix()
    # Prune only if the file sits under an ignored directory — match on a path-segment
    # boundary so `backend/.venv/...` is pruned without pruning `backend/app/...`.
    if any(rel == ig or rel.startswith(ig + "/") for ig in _IGNORED):
        return True
    return any(seg in "/" + rel for seg in PRUNE)


def _scan(globs) -> "list[tuple[str, str]]":
    """[(relpath, text)] for every readable file matching `globs`, pruned and deduped.

    Skips directories that happen to match a file glob and files that aren't valid
    UTF-8; either would otherwise abort the whole run.
    """
    out, seen = [], set()
    for pat in globs:
        for f in ROOT.glob(pat):
            rel = f.relative_to(ROOT).as_posix()
            if rel in seen or not f.is_file() or _pruned(f):
                continue
            seen.add(rel)
            try:
                out.append((rel, f.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, OSError):
                continue
    return out


def load_tags() -> dict:
    covered: dict[str, set] = {}
    for _rel, text in _scan(TEST_GLOBS):
        for sid, rid in SPEC_TAG.findall(text):
            covered.setdefault(sid, set()).add(rid)
    return covered


def load_tag_locs() -> dict:
    """(sid, rid) -> [ {file, line} ] — where each spec tag sits in the tests."""
    locs: dict[tuple, list] = {}
    for rel, text in _scan(TEST_GLOBS):
        for n, line in enumerate(text.splitlines(), 1):
            for sid, rid in SPEC_TAG.findall(line):
                locs.setdefault((sid, rid), []).append({"file": rel, "line": n})
    return locs


def load_feature_files() -> dict:
    """fid -> [ {file, line} ] — source files that declare `# feature: <id>`."""
    out: dict[str, list] = {}
    for rel, text in _scan(SRC_GLOBS):
        if "feature:" not in text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for fid in FEATURE_TAG.findall(line):
                out.setdefault(fid, []).append({"file": rel, "line": n})
    return out


def git_mtime(rel: str) -> int:
    """Unix time of the last commit touching rel, or 0 if unknown / not a git repo."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ct", "--", rel],
                           cwd=ROOT, capture_output=True, text=True, timeout=5)
        return int(r.stdout.strip()) if r.stdout.strip() else 0
    except (subprocess.SubprocessError, ValueError, OSError):
        return 0


# ── model ───────────────────────────────────────────────────────────────
def build():
    feats = load_features()
    specs = load_specs()
    tags = load_tags()
    tag_locs = load_tag_locs()
    feat_files = load_feature_files()
    goals, modules = load_goals(), load_modules()
    by_feature: dict[str, list] = {}
    for sid, s in specs.items():
        if s["feature"]:
            by_feature.setdefault(s["feature"], []).append(sid)

    for f in feats:
        sids = sorted(by_feature.get(f["id"], []))
        f["files"] = feat_files.get(f["id"], [])
        f["specs"] = []
        tot = cov = 0
        bare_any = False
        for sid in sids:
            rows = specs[sid]["rows"]
            cset = tags.get(sid, set())
            detail = specs[sid]["detail"]
            bare = [r for r in rows if r not in cset]
            entry = {
                "sid": sid, "file": specs[sid]["file"], "status": specs[sid]["status"],
                "rows_total": len(rows),
                "rows_cov": sum(1 for r in rows if r in cset), "rows_bare": bare,
                "rows_detail": [{"id": r, "cells": detail.get(r, []), "covered": r in cset,
                                 "tests": tag_locs.get((sid, r), [])}
                                for r in rows],
                "stale": _spec_stale(specs[sid]["file"], f["files"]),
            }
            f["specs"].append(entry)
            tot += entry["rows_total"]
            cov += entry["rows_cov"]
            bare_any = bare_any or not rows or bool(bare)
        f["rows_total"] = tot
        f["rows_cov"] = cov
        f["rows_bare"] = [r for e in f["specs"] for r in e["rows_bare"]]
        f["stale"] = any(e["stale"] for e in f["specs"])
        if not sids:
            f["state"] = "gray"
        else:
            f["state"] = "green" if tot and not bare_any else "red"
    return feats, specs, tags, goals, modules, by_feature


def _spec_stale(spec_file: str, files: list) -> bool:
    """True if any implementing source file was committed after the spec file."""
    if not files:
        return False
    smt = git_mtime(spec_file)
    if not smt:
        return False
    return any(git_mtime(x["file"]) > smt for x in files)


def to_model(feats, specs, goals, modules, issues):
    """Serializable computed model — the single artifact every renderer reads."""
    s = stats(feats)
    return {
        "generated_by": "trace.py",
        "stats": s,
        "audit": {"ok": not issues, "issues": issues, "warnings": gate_warnings(feats)},
        "modules": [{"module": m["module"], "proven": m["proven"], "total": m["total"],
                     "depends_on": m["depends_on"],
                     "features": [x["id"] for x in m["features"]]}
                    for m in by_module(feats, modules)],
        "module_graph": [{"module": mod, "depends_on": deps}
                         for mod, deps in sorted(modules.items())],
        "features": [
            {k: f[k] for k in ("id", "name", "module", "intent", "importance", "scope",
                               "state", "rows_cov", "rows_total", "files", "stale", "specs")}
            for f in feats],
        "deferred": [f["id"] for f in feats if f["scope"] == "deferred"],
    }


def audit_issues(feats, specs, tags, goals, modules):
    issues = []
    fids = {f["id"] for f in feats}
    for sid, s in specs.items():
        if s["feature"] and s["feature"] not in fids:
            issues.append(f"spec {sid}: feature {s['feature']} not in functions")
    for mod, deps in modules.items():
        for d in deps:
            if d not in modules:
                issues.append(f"architecture.md: module '{mod}' depends-on '{d}' — no such module")
    for f in feats:
        if modules and f["module"] not in modules:
            issues.append(f"{f['id']}: module '{f['module']}' not in architecture.md")
        if goals and f["intent"] not in goals:
            issues.append(f"{f['id']}: intent '{f['intent']}' not in intent.md")
    spec_ids = set(specs)
    for rel, text in _scan(TEST_GLOBS):
        name = rel.rsplit("/", 1)[-1]
        for sid, rid in SPEC_TAG.findall(text):
            if sid not in spec_ids:
                issues.append(f"{name}: `# spec: {sid} {rid}` — no such spec")
            elif rid not in specs[sid]["rows"]:
                issues.append(f"{name}: `# spec: {sid} {rid}` — {rid} not in {sid}")
    for fid, locs in load_feature_files().items():
        if fid not in fids:
            f0 = locs[0]
            issues.append(f"{f0['file']}:{f0['line']}: `# feature: {fid}` — not in functions")
    return issues


def gate_warnings(feats):
    """Non-fatal governance flags: code shipped ahead of an approved spec."""
    warns = []
    for f in feats:
        if f["scope"] != "active" or not f["files"]:
            continue
        n = len(f["files"])
        if not f["specs"]:
            warns.append(f"{f['id']}: {n} file(s) implement it but it has no spec (untraced code)")
            continue
        draft = [e["sid"] for e in f["specs"] if e["status"] != "approved"]
        if draft:
            warns.append(f"{f['id']}: {n} file(s) implement it but spec {', '.join(draft)} "
                         f"is not approved (code ahead of review)")
    return warns


def stats(feats):
    scope = [f for f in feats if f["scope"] == "active"]
    deferred = [f for f in feats if f["scope"] == "deferred"]
    by = lambda key, val, src=scope: sum(1 for f in src if f[key] == val)
    proven = by("state", "green")
    total = len(scope)
    rows_cov = sum(f["rows_cov"] for f in scope)
    rows_tot = sum(f["rows_total"] for f in scope)
    return {
        "total": total, "deferred": len(deferred),
        "must": by("importance", "must"), "should": by("importance", "should"),
        "could": by("importance", "could"),
        "green": by("state", "green"), "red": by("state", "red"),
        "gray": by("state", "gray"),
        "proven": proven, "pct": round(proven / total * 100) if total else 0,
        "must_proven": sum(1 for f in scope if f["importance"] == "must" and f["state"] == "green"),
        "must_total": by("importance", "must"),
        "rows_cov": rows_cov, "rows_tot": rows_tot,
        "rows_pct": round(rows_cov / rows_tot * 100) if rows_tot else 0,
    }


def by_module(feats, modules=None):
    modules = modules or {}
    mods: dict[str, list] = {}
    for f in feats:
        if f["scope"] == "active":
            mods.setdefault(f["module"], []).append(f)
    out = []
    for mod, mf in sorted(mods.items()):
        proven = sum(1 for f in mf if f["state"] == "green")
        out.append({"module": mod, "features": mf, "proven": proven, "total": len(mf),
                    "depends_on": modules.get(mod, [])})
    return out


# ── commands ────────────────────────────────────────────────────────────
def _print_warnings(warns):
    if warns:
        print(f"WARN: {len(warns)} governance flag(s) (non-blocking):", file=sys.stderr)
        for w in warns:
            print(f"   - {w}", file=sys.stderr)


def cmd_audit(_):
    feats, specs, tags, goals, modules, _bf = build()
    issues = audit_issues(feats, specs, tags, goals, modules)
    warns = gate_warnings(feats)
    if issues:
        print(f"FAIL: {len(issues)} broken link(s):", file=sys.stderr)
        for i in issues:
            print(f"   - {i}", file=sys.stderr)
        _print_warnings(warns)
        return 1
    _print_warnings(warns)   # warnings never change the exit code
    print(f"OK: all links resolve ({len(feats)} features, {len(specs)} specs)"
          + (f" · {len(warns)} warning(s)" if warns else ""))
    return 0


def cmd_approve(args):
    """Flip a spec's status to approved (the human gate — a deliberate act)."""
    target = SPECS / args.spec if (SPECS / args.spec).exists() else None
    if not target:
        for f in SPECS.glob("*.md"):
            m = FM.search(f.read_text())
            if m and _field(m.group(1), "id") == args.spec:
                target = f
                break
    if not target:
        print(f"no spec with id or filename '{args.spec}' under {SPECS}", file=sys.stderr)
        return 1
    text = target.read_text()
    if re.search(r"^status:\s*.+$", text, re.M):
        text = re.sub(r"^status:\s*.+$", "status: approved", text, count=1, flags=re.M)
    else:
        text = re.sub(r"^(---\n)", r"\1status: approved\n", text, count=1)
    target.write_text(text)
    print(f"approved {target.name}")
    return 0


def cmd_json(args):
    feats, specs, tags, goals, modules, _bf = build()
    issues = audit_issues(feats, specs, tags, goals, modules)
    m = to_model(feats, specs, goals, modules, issues)
    out = Path(args.out) if args.out else DOCS / "trace.json"
    out.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out} — {m['stats']['proven']}/{m['stats']['total']} proven, "
          f"audit {'OK' if m['audit']['ok'] else str(len(issues)) + ' broken'}")
    return 0 if m["audit"]["ok"] else 1


def cmd_report(_):
    feats, specs, tags, goals, modules, _bf = build()
    s = stats(feats)
    issues = audit_issues(feats, specs, tags, goals, modules)
    print(f"\nPROJECT — {s['total']} active features "
          f"({s['must']} must · {s['should']} should · {s['could']} could) · "
          f"{s['deferred']} deferred")
    print(f"STATE   — {s['green']} covered · {s['red']} spec-only · {s['gray']} untraced")
    print(f"COVER   — features {s['proven']}/{s['total']} ({s['pct']}%) · "
          f"must {s['must_proven']}/{s['must_total']} · "
          f"behavior rows {s['rows_cov']}/{s['rows_tot']} ({s['rows_pct']}%)")
    warns = gate_warnings(feats)
    print(f"AUDIT   — {'OK' if not issues else f'{len(issues)} broken'}"
          + (f" · {len(warns)} warning(s)" if warns else "") + "\n")
    for w in warns:
        print(f"  ! {w}")
    if warns:
        print()
    icon = {"green": "ok ", "red": "gap", "gray": "-- "}
    print(f"{'FEATURE':8} {'IMP':7} {'MODULE':14} {'ST':3} {'ROWS':6} NAME")
    print("-" * 76)
    for f in sorted(feats, key=lambda x: (x["scope"] != "active", x["module"], x["id"])):
        if f["scope"] == "deferred":
            continue
        rows = f"{f['rows_cov']}/{f['rows_total']}" if f["rows_total"] else "-"
        print(f"{f['id']:8} {f['importance']:7} {f['module'][:14]:14} "
              f"{icon[f['state']]:3} {rows:6} {f['name'][:30]}")
    return 0


# ── dashboard ───────────────────────────────────────────────────────────
CVAR = {"green": "var(--green)", "red": "var(--red)", "gray": "var(--gray)"}

CSS = """
:root{--bg:#f6f7f9;--panel:#fff;--ink:#141f30;--soft:#47566b;--mute:#818da0;--line:#e5e9ef;--ls:#d3dae3;--accent:#1e3a5f;--green:#2f9e5f;--red:#d64545;--gray:#9aa5b4;--gbg:#eaedf1;--mono:ui-monospace,"SF Mono",Menlo,monospace;--sans:system-ui,-apple-system,"Segoe UI",sans-serif;}
@media(prefers-color-scheme:dark){:root{--bg:#0c121c;--panel:#141d2b;--ink:#e9eef5;--soft:#a7b4c7;--mute:#6d7c92;--line:#212f3e;--ls:#2c3d4f;--accent:#6ea8dc;--green:#47c07d;--red:#e8706e;--gray:#6d7c92;--gbg:#1a2432;}}
:root[data-theme=light]{--bg:#f6f7f9;--panel:#fff;--ink:#141f30;--soft:#47566b;--mute:#818da0;--line:#e5e9ef;--ls:#d3dae3;--accent:#1e3a5f;--green:#2f9e5f;--red:#d64545;--gray:#9aa5b4;--gbg:#eaedf1;}
:root[data-theme=dark]{--bg:#0c121c;--panel:#141d2b;--ink:#e9eef5;--soft:#a7b4c7;--mute:#6d7c92;--line:#212f3e;--ls:#2c3d4f;--accent:#6ea8dc;--green:#47c07d;--red:#e8706e;--gray:#6d7c92;--gbg:#1a2432;}
*{box-sizing:border-box;}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1000px;margin:0 auto;padding:30px 22px 60px;}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap;}
h1{font-size:16px;margin:0;font-weight:650;}.sub{font-size:11.5px;color:var(--mute);margin-top:2px;}
.sub code,code.m{font-family:var(--mono);font-size:11px;}
.gen{font-family:var(--mono);font-size:10px;color:var(--mute);text-align:right;}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px;}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:15px 16px;}
.stat .k{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--mute);}
.stat .n{font-family:var(--mono);font-size:26px;font-weight:600;margin-top:8px;font-variant-numeric:tabular-nums;}
.stat .foot{font-size:11px;color:var(--soft);margin-top:4px;}
.bar{height:6px;border-radius:3px;background:var(--gbg);margin-top:10px;display:flex;overflow:hidden;}.bar>span{display:block;height:100%;}
h2{font-size:12.5px;margin:30px 0 4px;font-weight:650;}.note{font-size:11px;color:var(--mute);margin:0 0 12px;}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;}
.mod{padding:13px 16px;border-bottom:1px solid var(--line);}.mod:last-child{border-bottom:0;}
.mod .head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;}
.mod .name{font-weight:600;font-size:13.5px;}.mod .stat2{font-family:var(--mono);font-size:11.5px;color:var(--mute);}.mod .stat2 b{color:var(--green);}
.dep{font-family:var(--mono);font-size:10.5px;font-weight:400;color:var(--mute);margin-left:8px;}
.graphwrap{padding:18px 16px;overflow-x:auto;text-align:center;}
.mgsvg{max-width:100%;height:auto;}
.mtag{font-family:var(--mono);font-size:10.5px;color:var(--accent);border:1px solid var(--accent);border-radius:5px;padding:1px 6px;white-space:nowrap;}
.fid{font-family:var(--mono);font-size:10.5px;font-weight:600;color:var(--soft);background:var(--gbg);border-radius:5px;padding:1px 6px;white-space:nowrap;}
.pbar{display:flex;height:10px;border-radius:4px;overflow:hidden;margin:8px 0 8px;background:var(--gbg);}.pbar>span{display:block;}
.chips{display:flex;flex-wrap:wrap;gap:5px;}
.chip{font-family:var(--mono);font-size:10.5px;padding:2px 7px;border-radius:5px;border:1px solid var(--ls);display:inline-flex;align-items:center;gap:5px;color:var(--soft);}
.chip .d{width:6px;height:6px;border-radius:50%;}
.tblwrap{overflow-x:auto;}table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:760px;}
th{text-align:left;font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);font-weight:500;padding:10px 14px;border-bottom:1px solid var(--line);}
td{padding:10px 14px;border-bottom:1px solid var(--line);}tbody tr:last-child td{border-bottom:0;}
td.mono{font-family:var(--mono);font-variant-numeric:tabular-nums;}
.mute{color:var(--mute);font-family:var(--mono);font-size:11px;}td .mono{font-family:var(--mono);font-variant-numeric:tabular-nums;}
.specln{font-family:var(--mono);font-size:11px;color:var(--accent);text-decoration:none;border-bottom:1px solid var(--ls);}
.specln:hover{border-bottom-color:var(--accent);}
.specrow{padding:1px 0;}.specrow+.specrow{margin-top:3px;}
.stale{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.05em;color:#b26a00;background:#fff3e0;border:1px solid #f0c078;border-radius:4px;padding:1px 5px;}
@media(prefers-color-scheme:dark){.stale{color:#f0b866;background:#2e2410;border-color:#5a4520;}}
:root[data-theme=dark] .stale{color:#f0b866;background:#2e2410;border-color:#5a4520;}
.fchips{display:flex;flex-direction:column;gap:2px;}
.fchip{font-family:var(--mono);font-size:10.5px;color:var(--soft);}
.pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;}
.pill .d{width:6px;height:6px;border-radius:50%;}
.imp{font-family:var(--mono);font-size:10px;text-transform:uppercase;padding:2px 7px;border-radius:5px;background:var(--gbg);color:var(--soft);}
.imp.must{color:var(--red);font-weight:600;}
.audit{margin-top:14px;font-family:var(--mono);font-size:12px;padding:10px 14px;border-radius:9px;}
.audit.ok{background:var(--gbg);color:var(--soft);}.audit.bad{background:#fbe9e9;color:#b23b3b;border:1px solid #d64545;}
.audit.warn{background:#fff3e0;color:#b26a00;border:1px solid #f0c078;margin-top:8px;}
@media(prefers-color-scheme:dark){.audit.warn{background:#2e2410;color:#f0b866;border-color:#5a4520;}}
:root[data-theme=dark] .audit.warn{background:#2e2410;color:#f0b866;border-color:#5a4520;}
.status{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.05em;padding:1px 5px;border-radius:4px;border:1px solid var(--ls);color:var(--mute);}
.status.approved{color:var(--green);border-color:var(--green);}
.status.draft{color:var(--soft);}
.legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:14px;font-size:11px;color:var(--mute);}.legend span{display:inline-flex;align-items:center;gap:6px;}.legend i{width:9px;height:9px;border-radius:50%;}
.defer{margin-top:10px;font-size:11px;color:var(--mute);}.defer code{font-family:var(--mono);color:var(--soft);}
footer{margin-top:28px;padding-top:16px;border-top:1px solid var(--line);font-size:11.5px;color:var(--mute);}footer code{font-family:var(--mono);color:var(--soft);}
@media(max-width:680px){.stats{grid-template-columns:repeat(2,1fr);}}
.back{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--accent);text-decoration:none;margin-bottom:18px;}
.rblock{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:12px;}
.rblock.bare{border-color:var(--red);}
.rtop{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.rtop .rid{font-family:var(--mono);font-size:14px;font-weight:650;}
.gwt{display:grid;grid-template-columns:70px 1fr;gap:4px 14px;font-size:13px;margin-bottom:12px;}
.gwt .lbl{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);padding-top:2px;}
.gwt .val{color:var(--ink);line-height:1.5;}
.tests{border-top:1px dashed var(--line);padding-top:10px;}
.tests .th{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);margin-bottom:6px;}
.tlist{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px;}
.tlist li{font-family:var(--mono);font-size:12px;color:var(--soft);}
.tlist li .ln{color:var(--mute);}
.notest{font-family:var(--mono);font-size:12px;color:var(--red);}
"""


def _segbar(counts, total, css="bar"):
    if not total:
        return f'<div class="{css}"></div>'
    segs = "".join(
        f'<span style="width:{c/total*100:.1f}%;background:{CVAR[s]}"></span>'
        for s, c in counts if c)
    return f'<div class="{css}">{segs}</div>'


def _specfile(sid: str) -> str:
    return f"spec-{re.sub(r'[^A-Za-z0-9_-]', '_', sid)}.html"


def _module_layers(modules: dict) -> dict:
    """module -> layer index (longest path from a root); cycle-safe."""
    layer: dict[str, int] = {}

    def depth(n: str, seen: tuple) -> int:
        if n in layer:
            return layer[n]
        if n in seen:
            return 0  # break a cycle defensively
        deps = [d for d in modules.get(n, []) if d in modules]
        layer[n] = 0 if not deps else 1 + max(depth(d, seen + (n,)) for d in deps)
        return layer[n]

    for n in modules:
        depth(n, ())
    return layer


def _module_graph_html(modules: dict) -> str:
    """A layered DAG drawn as inline SVG (dep on top → dependent below). No JS/CDN."""
    if not any(deps for deps in modules.values()):
        return ""
    layer = _module_layers(modules)
    rows: dict[int, list] = {}
    for mod in sorted(modules):
        rows.setdefault(layer[mod], []).append(mod)

    NW, NH, HGAP, VGAP, PAD = 128, 34, 26, 58, 16
    ncols = max(len(v) for v in rows.values())
    nlayers = max(rows) + 1
    width = PAD * 2 + ncols * NW + (ncols - 1) * HGAP
    height = PAD * 2 + nlayers * NH + (nlayers - 1) * VGAP
    pos = {}  # module -> (cx, top-y)
    for l in sorted(rows):
        row = rows[l]
        row_w = len(row) * NW + (len(row) - 1) * HGAP
        x0 = (width - row_w) / 2  # center each layer
        y = PAD + l * (NH + VGAP)
        for i, mod in enumerate(row):
            x = x0 + i * (NW + HGAP)
            pos[mod] = (x + NW / 2, y)

    edges = ""
    for mod, deps in modules.items():
        for d in deps:
            if d not in pos or mod not in pos:
                continue
            x1, y1 = pos[d][0], pos[d][1] + NH   # bottom of upstream
            x2, y2 = pos[mod][0], pos[mod][1]     # top of dependent
            my = (y1 + y2) / 2
            edges += (f'<path d="M{x1:.0f},{y1:.0f} C{x1:.0f},{my:.0f} {x2:.0f},{my:.0f} '
                      f'{x2:.0f},{y2:.0f}" fill="none" stroke="var(--ls)" stroke-width="1.5" '
                      f'marker-end="url(#mg-arr)"/>')
    nodes = ""
    for mod, (cx, y) in pos.items():
        nodes += (f'<g><rect x="{cx - NW / 2:.0f}" y="{y}" width="{NW}" height="{NH}" rx="7" '
                  f'fill="var(--panel)" stroke="var(--ls)"/>'
                  f'<text x="{cx:.0f}" y="{y + NH / 2 + 4:.0f}" text-anchor="middle" '
                  f'font-family="var(--mono)" font-size="11.5" fill="var(--ink)">{mod}</text></g>')

    svg = (f'<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" '
           f'height="{height:.0f}" class="mgsvg" role="img" aria-label="module dependency graph">'
           '<defs><marker id="mg-arr" markerWidth="9" markerHeight="9" refX="7" refY="3" '
           'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="var(--mute)"/></marker></defs>'
           f'{edges}{nodes}</svg>')
    return ('<h2>Module dependencies</h2>'
            '<p class="note">Each box is a <span class="mtag">module</span>. Upstream modules sit '
            'above the modules that <code>depends-on</code> them — a break high in the graph puts '
            'everything below it at risk.</p>'
            f'<div class="panel graphwrap">{svg}</div>')


# behavior-table headers to try, in order; falls back to Cell 1/2/3…
_GWT = ["Given", "When", "Then"]


def build_spec_page(f: dict, e: dict, tag_locs: dict) -> str:
    sid = e["sid"]
    blocks = ""
    for r in e["rows_detail"]:
        cells = [c for c in r["cells"] if c]
        gwt = ""
        for i, c in enumerate(cells):
            lbl = _GWT[i] if i < len(_GWT) else f"Cell {i + 1}"
            gwt += f'<div class="lbl">{lbl}</div><div class="val">{c}</div>'
        locs = tag_locs.get((sid, r["id"]), [])
        if locs:
            items = "".join(
                f'<li>{l["file"]}<span class="ln">:{l["line"]}</span></li>' for l in locs)
            tests = (f'<div class="tests"><div class="th">Covering tests '
                     f'({len(locs)})</div><ul class="tlist">{items}</ul></div>')
        else:
            tests = ('<div class="tests"><div class="th">Covering tests</div>'
                     '<div class="notest">none — this rule is not proven by any test</div></div>')
        c = "green" if r["covered"] else "red"
        st = "covered" if r["covered"] else "no test"
        blocks += (
            f'<div class="rblock {"" if r["covered"] else "bare"}"><div class="rtop">'
            f'<span class="rid">{r["id"]}</span>'
            f'<span class="pill" style="color:{CVAR[c]}"><span class="d" style="background:{CVAR[c]}"></span>{st}</span>'
            f'</div><div class="gwt">{gwt}</div>{tests}</div>')
    return f"""<title>{project_name()} · {sid} — spec</title>
<meta name="description" content="Behavior rules of {sid} and the tests covering each rule.">
<style>{CSS}</style>
<div class="wrap">
  <a class="back" href="dashboard.html">&larr; dashboard</a>
  <div class="top"><div>
    <h1>{sid}</h1>
    <div class="sub">feature <code>{f["id"]} {f["name"]}</code> · module <code>{f["module"]}</code> ·
    status <code>{e["status"]}</code> · <code>{e["rows_cov"]}/{e["rows_total"]}</code> rules proven
    {'· <span class="stale">stale — code changed after this spec</span>' if e["stale"] else ''}</div>
    <div class="sub">implemented in: {", ".join(f'<code>{x["file"]}</code>' for x in f["files"]) or "<span class=mute>no file declares this feature</span>"}</div>
  </div></div>
  <h2>Behavior rules</h2>
  <p class="note">Each rule (Rn) and the tests that tag it with <code>#&nbsp;spec: {sid} Rn</code>.</p>
  {blocks}
  <footer>Generated by <code>trace.py dashboard</code>. A rule is "covered" when a test names
  it — not a guarantee the test passes or is correct.</footer>
</div>
"""


def cmd_dashboard(args):
    feats, specs, tags, goals, modules, _bf = build()
    tag_locs = load_tag_locs()
    s = stats(feats)
    issues = audit_issues(feats, specs, tags, goals, modules)
    deferred = [f for f in feats if f["scope"] == "deferred"]

    statecounts = [("green", s["green"]), ("red", s["red"]), ("gray", s["gray"])]

    # per-module rollup
    mods_html = ""
    for m in by_module(feats, modules):
        chips = "".join(
            f'<span class="chip"><span class="d" style="background:{CVAR[f["state"]]}"></span>'
            f'<span class="fid">{f["id"]}</span> {f["name"]}</span>'
            for f in m["features"])
        mc = [(st, sum(1 for f in m["features"] if f["state"] == st)) for st in ("green", "red", "gray")]
        dep = (f'<span class="dep">depends on {", ".join(m["depends_on"])}</span>'
               if m["depends_on"] else "")
        mods_html += (
            f'<div class="mod"><div class="head"><span class="name"><span class="mtag">{m["module"]}</span>{dep}</span>'
            f'<span class="stat2"><b>{m["proven"]}</b> / {m["total"]} proven</span></div>'
            f'{_segbar(mc, m["total"], "pbar")}<div class="chips">{chips}</div></div>')

    # module dependency graph (all modules, edges from depends-on)
    graph_html = _module_graph_html(modules)

    # per-feature matrix
    rows_html = ""
    ICON = {"green": ("", "covered"), "red": ("", "spec-only"), "gray": ("", "untraced")}
    for f in sorted([x for x in feats if x["scope"] == "active"],
                    key=lambda x: (x["state"] != "gray", x["module"], x["id"])):
        ic, lbl = ICON[f["state"]]
        impcls = "imp must" if f["importance"] == "must" else "imp"
        if f["specs"]:
            lines = []
            for e in f["specs"]:
                rows = f'{e["rows_cov"]}/{e["rows_total"]}'
                bare = (" · bare: " + ", ".join(e["rows_bare"])) if e["rows_bare"] else ""
                stale = ' <span class="stale">stale</span>' if e["stale"] else ""
                st = ('<span class="status approved">approved</span>'
                      if e["status"] == "approved"
                      else '<span class="status draft">draft</span>')
                lines.append(
                    f'<div class="specrow"><a class="specln" href="{_specfile(e["sid"])}">{e["sid"]}</a> '
                    f'{st} <span class="mono">{rows}</span>{bare}{stale}</div>')
            spec_cell = "".join(lines)
        else:
            spec_cell = '<span class="mute">no spec</span>'
        if f["files"]:
            fl = "".join(f'<span class="fchip">{x["file"]}</span>' for x in f["files"])
            files_cell = f'<div class="fchips">{fl}</div>'
        else:
            files_cell = '<span class="mute">—</span>'
        rows_html += (
            f'<tr><td><span class="fid">{f["id"]}</span></td><td>{f["name"]}</td>'
            f'<td><span class="mtag">{f["module"]}</span></td>'
            f'<td><span class="{impcls}">{f["importance"]}</span></td>'
            f'<td><span class="pill" style="color:{CVAR[f["state"]]}"><span class="d" style="background:{CVAR[f["state"]]}"></span>{lbl}</span></td>'
            f'<td>{files_cell}</td>'
            f'<td>{spec_cell}</td></tr>')

    audit_html = (f'<div class="audit ok">OK — all links resolve</div>'
                  if not issues else
                  f'<div class="audit bad">FAIL — {len(issues)} broken link(s): '
                  + "; ".join(issues[:4]) + ("…" if len(issues) > 4 else "") + "</div>")
    warns = gate_warnings(feats)
    warn_html = (f'<div class="audit warn">{len(warns)} governance flag(s) (non-blocking): '
                 + "; ".join(warns[:4]) + ("…" if len(warns) > 4 else "") + "</div>") if warns else ""
    defer_html = (f'<div class="defer">deferred (out of scope): '
                  + " · ".join(f'<code>{f["id"]}</code>' for f in deferred) + "</div>") if deferred else ""

    proj = project_name()
    html = f"""<title>{proj} — traceability</title>
<meta name="description" content="{proj}: per-feature test coverage, per-module rollup, and integrity — generated by trace.py (no LLM).">
<style>{CSS}</style>
<div class="wrap">
  <div class="top">
    <div><h1>{proj}</h1><div class="sub">test traceability · <code>functions</code> × <code>specs</code> × <code>#&nbsp;spec:</code> tags</div></div>
    <div class="gen">generated · no LLM<br>trace.py dashboard</div>
  </div>

  <div class="stats">
    <div class="stat"><div class="k">Features (active)</div><div class="n">{s['total']}</div>
      <div class="foot">{s['must']} must · {s['should']} should · {s['could']} could</div>
      <div class="bar"><span style="width:100%;background:var(--accent)"></span></div></div>
    <div class="stat"><div class="k">Proven</div><div class="n" style="color:var(--green)">{s['pct']}<span style="font-size:15px;color:var(--mute)">%</span></div>
      <div class="foot">{s['proven']} / {s['total']} features covered</div>
      {_segbar(statecounts, s['total'])}</div>
    <div class="stat"><div class="k">Must covered</div><div class="n">{s['must_proven']}<span style="font-size:15px;color:var(--mute)">/{s['must_total']}</span></div>
      <div class="foot">client-critical features proven</div>
      <div class="bar"><span style="width:{(s['must_proven']/s['must_total']*100) if s['must_total'] else 0:.0f}%;background:var(--red)"></span></div></div>
    <div class="stat"><div class="k">Behavior rows</div><div class="n">{s['rows_pct']}<span style="font-size:15px;color:var(--mute)">%</span></div>
      <div class="foot">{s['rows_cov']} / {s['rows_tot']} Rn covered</div>
      <div class="bar"><span style="width:{s['rows_pct']}%;background:var(--green)"></span></div></div>
  </div>
  {audit_html}
  {warn_html}
  {defer_html}

  <h2>Coverage by module</h2>
  <p class="note">A <span class="mtag">module</span> is <em>where code lives</em> (a pipeline
  stage / screen / service). The chips inside are its <span class="fid">features</span> — the
  product capabilities that live there. This shows how many of each module's features are proven.</p>
  <div class="panel">{mods_html}</div>

  {graph_html}

  <h2>Feature matrix</h2>
  <p class="note">Per feature: module, importance, state, the source files that declare <code>#&nbsp;feature:</code>, and its specs' behavior-row coverage. Click a spec id to open its rule-by-rule page.</p>
  <div class="panel"><div class="tblwrap"><table>
    <thead><tr><th>id</th><th>feature</th><th>module</th><th>imp</th><th>state</th><th>files</th><th>spec · rows (cov/total)</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table></div></div>

  <div class="legend">
    <span><i style="background:var(--green)"></i>covered — every Rn has a test</span>
    <span><i style="background:var(--red)"></i>spec-only — a bare Rn</span>
    <span><i style="background:var(--gray)"></i>untraced — no spec</span>
  </div>

  <footer><strong>How.</strong> <code>trace.py</code> joins <code>functions.md</code> +
  <code>specs/*.md</code> + <code>#&nbsp;spec:</code> tags and computes state — no LLM, no test run.
  "covered" means a test <em>claims</em> the Rn, not that it passes or is correct (see FRAMEWORK-NOTES.md).</footer>
</div>
"""
    out = Path(args.out) if args.out else DOCS / "dashboard.html"
    out.write_text(html)
    npages = 0
    for f in feats:
        for e in f["specs"]:
            (out.parent / _specfile(e["sid"])).write_text(build_spec_page(f, e, tag_locs))
            npages += 1
    print(f"wrote {out} (+ {npages} spec pages) — {s['proven']}/{s['total']} proven, "
          f"must {s['must_proven']}/{s['must_total']}, rows {s['rows_pct']}%")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Test-traceability tool (one file).")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("audit", help="check every link resolves; non-zero exit on a break")
    sub.add_parser("report", help="terminal: project stats + per-feature table")
    j = sub.add_parser("json", help="write docs/trace.json (the computed model)")
    j.add_argument("-o", "--out", help="output path (default docs/trace.json)")
    d = sub.add_parser("dashboard", help="write docs/dashboard.html + spec pages")
    d.add_argument("-o", "--out", help="output path (default docs/dashboard.html)")
    a = sub.add_parser("approve", help="flip a spec's status to approved (the human gate)")
    a.add_argument("spec", help="spec id (SPEC-...) or filename under docs/specs/")
    args = ap.parse_args()
    return {"audit": cmd_audit, "report": cmd_report, "json": cmd_json,
            "dashboard": cmd_dashboard, "approve": cmd_approve}.get(args.cmd, cmd_report)(args)


if __name__ == "__main__":
    raise SystemExit(main())
