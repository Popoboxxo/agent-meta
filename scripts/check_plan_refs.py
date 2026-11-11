#!/usr/bin/env python3
"""check_plan_refs.py - check files, symbols and issues named in plans against a git ref.

Usage:
  python3 scripts/check_plan_refs.py --plans <file-or-dir>... [--repo PATH]
      [--ref origin/main] [--no-issues] [--json] [--gh PATH]

Reads only git state of --ref (ls-tree / show / grep), never the working tree.
Exit: 0 = no ERROR, 1 = at least one ERROR, 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

_EXT = r"(?:py|md|yaml|yml|json|sh|html)"
_PATH_RE = re.compile(
    r"(?<![\w/.:~$-])((?:[\w.-]+/)+[\w.-]*\.%s(?![\w*])|(?:[\w.-]+/)+)(?::(\d+)(?:-(\d+))?)?" % _EXT
)
_TICK_RE = re.compile(r"`([^`]+)`")
_ISSUE_RE = re.compile(r"#(\d+)(?![\w])")
_SYM_RE = re.compile(r"[A-Za-z_]\w*")
_MODE_SPLIT_RE = re.compile(r"(?=\b(?:Create|Modify|Delete|Test)\b[: ])")
_DONE_RE = re.compile(r"\[x\]|erledigt|done|closed|merged|geschlossen|gemergt", re.I)
_SKIP_LINE_RE = re.compile(r"existiert nicht|geplant")
_FILES_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(?:Files:|Create|Modify|Test|Delete)")
_DRIFT_TOLERANCE = 10
_GH_FALLBACK = "/home/hermes/.local/bin/gh"


def _is_symbol(tok: str) -> Optional[str]:
    """Return the searchable symbol name for a token shaped like code, else None."""
    call = tok.endswith("()")
    name = tok[:-2] if call else tok
    last = name.split(".")[-1]
    if not _SYM_RE.fullmatch(last) or not all(_SYM_RE.fullmatch(p) for p in name.split(".")):
        return None
    camel = any(c.isupper() for c in last[1:]) and any(c.islower() for c in last)
    return last if (call or "_" in last or camel) else None


def _paths_in(text: str) -> list:
    out = []
    for seg in _MODE_SPLIT_RE.split(text):
        create = seg.startswith("Create")
        strict = seg.startswith(("Modify", "Delete"))
        for m in _PATH_RE.finditer(seg):
            p = m.group(1)
            if p.startswith(".tmp/") or "{{" in p:
                continue
            lines = None
            if m.group(2):
                lines = (int(m.group(2)), int(m.group(3) or m.group(2)))
            out.append({"path": p, "lines": lines, "create": create, "strict": strict, "end": m.end(), "seg": seg})
    return out


def extract_refs(markdown: str) -> List[dict]:
    """Extract path/symbol/issue refs from plan markdown (conservative)."""
    refs: Dict[tuple, dict] = {}
    in_fence = in_frische = False

    def add(key: tuple, rec: dict) -> None:
        if key in refs:
            refs[key]["done"] = refs[key].get("done", False) or rec.get("done", False)
        else:
            refs[key] = rec

    for no, line in enumerate(markdown.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.match(r"#{1,3} ", line):
            in_frische = line.startswith("## Frische-Check")
            continue
        if _SKIP_LINE_RE.search(line):
            continue
        raw = in_frische or bool(_FILES_LINE_RE.match(line))
        ticks = _TICK_RE.findall(line)
        text = line.replace("`", "") if raw else " ".join(ticks)
        paths = _paths_in(text)
        done = bool(_DONE_RE.search(line))
        for p in paths:
            add(("path", p["path"], p["lines"], p["create"]),
                {"kind": "path", "ref": p["path"], "line": no, "lines": p["lines"], "create": p["create"],
                 "strict": in_frische or p["strict"]})
        if any(p["create"] for p in paths):
            continue
        for m in _ISSUE_RE.finditer(text if raw else " ".join(ticks)):
            add(("issue", m.group(1)), {"kind": "issue", "ref": "#" + m.group(1), "line": no, "done": done})
        syms = []
        for t in ticks:
            s = None if "/" in t else _is_symbol(t.strip())
            if s:
                syms.append(s)
        if raw:
            full = text
            syms += [m.group(1) for m in re.finditer(r"::([A-Za-z_]\w*)", full)]
            for p in paths:
                rest = full[full.find(p["path"]) + len(p["path"]):]
                if rest.startswith(": ") or rest.startswith(":\t"):
                    for piece in rest[1:].split(","):
                        s = _is_symbol(piece.strip())
                        if s:
                            syms.append(s)
        files = [p["path"] for p in paths if not p["create"] and not p["path"].endswith("/")]
        anchors = [(p["path"], p["lines"][0]) for p in paths if p["lines"]]
        for s in dict.fromkeys(syms):
            add(("symbol", s, tuple(files)),
                {"kind": "symbol", "ref": s, "line": no, "files": files, "anchors": anchors,
                 "frische": in_frische})
    return list(refs.values())


class Repo:
    """Read-only view of one git ref."""

    def __init__(self, path: str, ref: str) -> None:
        self.path, self.ref = path, ref
        self._blobs: Dict[str, Optional[List[str]]] = {}
        self._found: set = set()
        self._searched: set = set()
        r = self._git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
        if r.returncode != 0:
            raise ValueError("unknown ref %r in repo %s" % (ref, path))
        r = self._git("ls-tree", "-r", "--name-only", ref)
        self.files = set(r.stdout.splitlines())
        self.dirs = {"/".join(f.split("/")[:i]) + "/" for f in self.files for i in range(1, f.count("/") + 1)}

    def _git(self, *args: str) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(["git", "-C", self.path, *args], capture_output=True, text=True,
                              errors="replace")

    def exists(self, p: str) -> bool:
        return p in self.files or (p.endswith("/") and p in self.dirs)

    def lines(self, p: str) -> Optional[List[str]]:
        if p not in self._blobs:
            r = self._git("show", "%s:%s" % (self.ref, p))
            self._blobs[p] = r.stdout.splitlines() if r.returncode == 0 else None
        return self._blobs[p]

    def grep_any(self, sym: str) -> bool:
        if sym not in self._found:
            self.prefetch([sym])
        return sym in self._found

    def prefetch(self, symbols: List[str]) -> None:
        """One batched git grep per 100 symbols instead of one per symbol (speed)."""
        todo = [x for x in dict.fromkeys(symbols) if x not in self._found and x not in self._searched]
        for i in range(0, len(todo), 100):
            chunk = todo[i:i + 100]
            args = [a for x in chunk for a in ("-e", x)]
            r = self._git("grep", "-h", "-o", "-w", "-F", "-I", *args, self.ref, "--")
            self._found.update(set(r.stdout.split()) & set(chunk))
            self._searched.update(chunk)


def default_issue_runner(gh: str, repo: str) -> Callable[[int], Optional[str]]:
    """Return state string, None if the issue does not exist, raise RuntimeError otherwise."""
    def run(n: int) -> Optional[str]:
        r = subprocess.run([gh, "issue", "view", str(n), "--json", "state", "-q", ".state"],
                           capture_output=True, text=True, cwd=repo)
        if r.returncode == 0:
            return r.stdout.strip()
        if "Could not resolve" in r.stderr or "not found" in r.stderr.lower():
            return None
        raise RuntimeError(r.stderr.strip() or "gh failed")
    return run


def _f(cls: str, sev: str, ref: str, line: int, msg: str, hint: str = "") -> dict:
    return {"cls": cls, "sev": sev, "ref": ref, "line": line, "msg": msg, "hint": hint}


def check_refs(refs: List[dict], repo: Repo, issue_runner: Optional[Callable]) -> List[dict]:
    out: List[dict] = []
    cache: Dict[int, object] = {}
    repo.prefetch([r["ref"] for r in refs if r["kind"] == "symbol" and not r["files"]])
    for r in refs:
        k, ref, ln = r["kind"], r["ref"], r["line"]
        if k == "path":
            if r["create"]:
                if not ref.endswith("/") and repo.exists(ref):
                    out.append(_f("CREATE_EXISTS", "WARN", ref, ln, "marked Create but exists at ref"))
            elif ref.endswith("/"):
                continue  # shortcut: directories are only checked for Create, not for existence
            elif not repo.exists(ref):
                # prose mentions may name planned files; only Frische/Modify/Delete are hard errors
                out.append(_f("FILE_MISSING", "ERROR" if r["strict"] else "WARN", ref, ln,
                              "not in tree at ref"))
            elif r["lines"] and (content := repo.lines(ref)) is not None and r["lines"][0] > len(content):
                out.append(_f("LINE_OUT_OF_RANGE", "WARN", "%s:%d" % (ref, r["lines"][0]), ln,
                              "file has %d lines" % len(content)))
        elif k == "symbol":
            out.extend(_check_symbol(r, repo))
        elif k == "issue" and issue_runner is not None:
            n = int(ref[1:])
            if n not in cache:
                try:
                    cache[n] = issue_runner(n)
                except RuntimeError as exc:
                    cache[n] = exc
            state = cache[n]
            if isinstance(state, RuntimeError):
                out.append(_f("ISSUE_CHECK_FAILED", "WARN", ref, ln, str(state)))
            elif state is None:
                out.append(_f("ISSUE_MISSING", "ERROR", ref, ln, "gh cannot resolve it"))
            elif state in ("CLOSED", "MERGED") and not r.get("done"):
                out.append(_f("ISSUE_CLOSED", "INFO", ref, ln, "state %s" % state))
    return out


def _check_symbol(r: dict, repo: Repo) -> List[dict]:
    sym, ln = r["ref"], r["line"]
    rx = re.compile(r"(?<!\w)%s(?!\w)" % re.escape(sym))
    files = [f for f in r["files"] if f in repo.files]
    if not r["files"]:
        if repo.grep_any(sym):
            return []
        return [_f("SYMBOL_MISSING", "WARN", sym, ln, "not found anywhere at ref")]
    if not files:
        return []  # FILE_MISSING already reported
    hits = {f: [i for i, t in enumerate(repo.lines(f) or [], 1) if rx.search(t)] for f in files}
    if not any(hits.values()):
        sev = "ERROR" if r["frische"] else "WARN"
        return [_f("SYMBOL_MISSING", sev, sym, ln, "not in %s" % ", ".join(files))]
    for path, start in r["anchors"]:
        if path in hits and hits[path] and min(abs(h - start) for h in hits[path]) > _DRIFT_TOLERANCE:
            actual = min(hits[path], key=lambda h: abs(h - start))
            return [_f("ANCHOR_DRIFT", "WARN", "%s:%d" % (path, start), ln,
                       "%s not within +-%d lines" % (sym, _DRIFT_TOLERANCE), "now at %s:%d" % (path, actual))]
    return []


def _collect_plans(items: List[str]) -> List[Path]:
    plans: List[Path] = []
    for it in items:
        p = Path(it)
        plans += sorted(p.glob("*.md")) if p.is_dir() else ([p] if p.is_file() else [])
    return plans


def _print_table(name: str, nrefs: int, findings: List[dict]) -> None:
    print("\n== %s (%d refs) ==" % (name, nrefs))
    print("Klasse | Referenz | Zeile im Plan | Befund | Vorschlag")
    for f in findings:
        print("%s [%s] | %s | %d | %s | %s" % (f["cls"], f["sev"], f["ref"], f["line"], f["msg"], f["hint"]))


def main(argv: Optional[List[str]] = None, issue_runner: Optional[Callable] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plans", nargs="+", required=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--no-issues", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gh")
    args = ap.parse_args(argv)

    plans = _collect_plans(args.plans)
    if not plans:
        print("error: no plan files found in %s" % args.plans, file=sys.stderr)
        return 2
    try:
        repo = Repo(args.repo, args.ref)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    runner = None
    if not args.no_issues:
        runner = issue_runner
        if runner is None:
            gh = args.gh or shutil.which("gh") or (_GH_FALLBACK if Path(_GH_FALLBACK).exists() else None)
            if not gh:
                print("error: gh not found; pass --gh or --no-issues", file=sys.stderr)
                return 2
            runner = default_issue_runner(gh, args.repo)

    report = []
    for p in plans:
        refs = extract_refs(p.read_text(encoding="utf-8", errors="replace"))
        report.append({"plan": str(p), "refs": len(refs), "findings": check_refs(refs, repo, runner)})
    count = lambda sev: sum(f["sev"] == sev for r in report for f in r["findings"])  # noqa: E731
    summary = {"errors": count("ERROR"), "warns": count("WARN"), "infos": count("INFO")}
    if args.json:
        print(json.dumps({"ref": args.ref, "plans": report, "summary": summary}, indent=2))
    else:
        for r in report:
            _print_table(r["plan"], r["refs"], r["findings"])
        print("\nSummary: %(errors)d ERROR, %(warns)d WARN, %(infos)d INFO" % summary)
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
