#!/usr/bin/env python3
"""workflow-lint: no `${{ }}` expression is pasted into anything that runs.

THE POLICY IS ABSOLUTE (ORCA ruling, 2026-11-14): whoever controls the value, an expression
may not be pasted into `run:`, `script:`, `shell:`, `container.options` or `docker://` args.
Only `env:` (then "$VAR" / process.env.X) passes. An allowlist shape fails closed; a taint
classifier fails open on the case it misjudges.

Three engines, one verdict:
  1. zizmor (template-injection), --persona=pedantic --min-severity=informational --no-config:
     every severity fails, runner-set contexts included. Covers run:, github-script script:,
     composite actions and every YAML spelling (measured, GITOPS board dc42e3a).
  2. actionlint, [expression] findings only: rejects a context where GitHub allows none, which
     is how a custom `shell:` with ${{ }} is caught.
  3. this file, for the two sinks neither tool checks: job/service `container.options` and a
     `docker://` step's `with:` args/entrypoint.

Exceptions: only a per-line `# zizmor: ignore[template-injection] -- reason: <why>`, each
listed in the output for review. A bare ignore (no reason) fails. A zizmor config file that
disables or ignores template-injection fails, and configs are not read anyway (--no-config).

  lint.py --root DIR --zizmor BIN --actionlint BIN
Exit 0 only when every engine reports nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

EXPR = re.compile(r"\$\{\{")
IGNORE = re.compile(r"zizmor:\s*ignore\[([^\]]*)\](.*)$")
REASON = re.compile(r"^\s*--\s*reason:\s*\S.{8,}")  # a written reason, at least ~10 characters
CONFIG_NAMES = ("zizmor.yml", "zizmor.yaml", ".github/zizmor.yml", ".github/zizmor.yaml")
ACTIONLINT_CONFIGS = (".github/actionlint.yaml", ".github/actionlint.yml")


def collect(root: Path) -> tuple[list[Path], list[Path]]:
    wf = sorted(p for p in (root / ".github" / "workflows").glob("*") if p.suffix in (".yml", ".yaml"))
    actions = sorted(p for p in root.rglob("action.y*ml")
                     if ".git" not in p.parts and "node_modules" not in p.parts and p.suffix in (".yml", ".yaml"))
    return wf, actions


def blanket_configs(root: Path) -> list[str]:
    out = [f"{name}: an actionlint config can ignore findings; the gate runs actionlint with its own empty config, so remove it"
           for name in ACTIONLINT_CONFIGS if (root / name).is_file() and "ignore" in (root / name).read_text()]
    for name in CONFIG_NAMES:
        p = root / name
        if p.is_file() and "template-injection" in p.read_text():
            out.append(f"{name}: a zizmor config names template-injection; blanket ignores are refused (use a per-line ignore with a reason)")
    return out


def inline_ignores(files: list[Path], root: Path) -> tuple[list[str], list[str]]:
    bad, listed = [], []
    for f in files:
        for n, line in enumerate(f.read_text().splitlines(), 1):
            m = IGNORE.search(line)
            if not m or "template-injection" not in m.group(1):
                continue
            where = f"{f.relative_to(root)}:{n}"
            if REASON.match(m.group(2)):
                listed.append(f"{where}: {m.group(2).strip()}")
            else:
                bad.append(f"{where}: zizmor ignore[template-injection] without a written reason (`-- reason: …`)")
    return bad, listed


def zizmor(binary: str, files: list[Path], root: Path) -> list[str]:
    if not files:
        return []
    # Run FROM the repo root, as the action does: zizmor discovers a repo's zizmor.yml relative to
    # its working directory, so that's where --no-config has to be proven to hold.
    o = subprocess.run([binary, "--offline", "--no-config", "--persona=pedantic", "--min-severity=informational",
                        "--format=json", *(str(f.relative_to(root)) for f in files)],
                       capture_output=True, text=True, cwd=root)
    try:
        findings = json.loads(o.stdout or "null")
        assert isinstance(findings, list)
    except (ValueError, AssertionError):
        # Fail closed: a zizmor that could not audit (a parse error, a crash) is not a pass.
        return [f"zizmor did not produce a report (exit {o.returncode}): {o.stderr.strip()[-300:]}"]
    out = []
    for x in findings:
        if x.get("ident") != "template-injection":
            continue
        for loc in x["locations"]:
            ann = loc["symbolic"].get("annotation", "")
            if "expand" in ann or "via this input" in ann:
                key = loc["symbolic"]["key"].get("Local", {})
                path = Path(key.get("given_path") or key.get("verbatim_path") or "?")
                try:
                    path = path.resolve().relative_to(root.resolve())
                except ValueError:
                    pass
                out.append(f"{path}:{loc['concrete']['location']['start_point']['row'] + 1}: "
                           f"template-injection ({x['determinations']['severity']}): {ann}")
    return sorted(set(out))


# actionlint types a reusable workflow's `with:` LITERALS by their YAML text and ignores quoting:
# `dry_run: "true"` into a `type: string` input is reported as "bool value cannot be assigned"
# (measured, 1.7.12: "true", 'true', true and "false" all flagged; "yes" and "1" not). That is a type
# check on a literal, never an expression in a sink, so it is the ONE [expression] message this gate
# drops. Every other [expression] finding still fails: the drop is one exact shape, not a class.
LITERAL_INPUT_TYPE = re.compile(r'^input "[^"]+" is typed as \w+ by reusable workflow "[^"]+"\. \w+ value cannot be assigned$')


def actionlint(binary: str, files: list[Path], root: Path) -> list[str]:
    if not files:
        return []
    # actionlint also reads a repo's .github/actionlint.yaml, whose `ignore:` patterns would silence
    # it. Give it an empty config of ours instead, and run from the repo root like zizmor.
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as cfg:
        cfg.write("{}\n")
    try:
        o = subprocess.run([binary, "-no-color", "-config-file", cfg.name, "-format", "{{json .}}",
                            *(str(f.relative_to(root)) for f in files)], capture_output=True, text=True, cwd=root)
    finally:
        Path(cfg.name).unlink(missing_ok=True)
    try:
        errs = json.loads(o.stdout or "[]")
    except ValueError:
        return [f"actionlint did not produce a report (exit {o.returncode}): {o.stderr.strip()[-300:]}"]
    return [f"{e['filepath']}:{e['line']}: actionlint [{e['kind']}]: {e['message']}"
            for e in errs if e.get("kind") == "expression" and not LITERAL_INPUT_TYPE.match(e.get("message", ""))]


def unparseable(files: list[Path], root: Path) -> list[str]:
    """zizmor SKIPS a file it can't parse (a WARN) and audits the rest: measured, 1.32.0. A file
    nobody audited is not a pass, so any file that isn't valid YAML fails here."""
    out = []
    for f in files:
        try:
            yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            out.append(f"{f.relative_to(root)}: could not parse as YAML, so nothing audited it ({str(e).splitlines()[0]})")
    return out


def uncovered_sinks(files: list[Path], root: Path) -> list[str]:
    """The two sinks zizmor and actionlint don't check (measured): container options, docker:// args."""
    out = []
    for f in files:
        try:
            doc = yaml.safe_load(f.read_text()) or {}
        except yaml.YAMLError:
            continue  # reported by unparseable()
        for jname, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            containers = [("container", job.get("container"))] + [(f"services.{k}", v) for k, v in (job.get("services") or {}).items()]
            for label, c in containers:
                if isinstance(c, dict) and EXPR.search(str(c.get("options", ""))):
                    out.append(f"{f.relative_to(root)}: job {jname!r} {label}.options holds an expression (docker create options)")
            for i, s in enumerate(job.get("steps") or []):
                if isinstance(s, dict) and str(s.get("uses", "")).startswith("docker://"):
                    w = s.get("with") or {}
                    for k in ("args", "entrypoint"):
                        if EXPR.search(str(w.get(k, ""))):
                            out.append(f"{f.relative_to(root)}: job {jname!r} step {s.get('name') or i!r}: docker:// with.{k} holds an expression")
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--zizmor", required=True)
    ap.add_argument("--actionlint", required=True)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    wf, actions = collect(root)
    files = wf + actions
    if not files:
        print("::error::workflow-lint found no workflow or action file under", root)
        return 1
    bad_ign, listed = inline_ignores(files, root)
    problems = (blanket_configs(root) + bad_ign + unparseable(files, root) + zizmor(a.zizmor, files, root)
                + actionlint(a.actionlint, wf, root) + uncovered_sinks(wf, root))
    print(f"workflow-lint: {len(wf)} workflow(s), {len(actions)} action file(s)")
    for line in listed:
        print(f"  reviewed exception: {line}")
    for p in problems:
        print(f"::error::{p}")
    if problems:
        print(f"🔴 {len(problems)} finding(s). Pass each value through env: and read it as \"$VAR\" / process.env.X.")
        return 1
    print("✓ no expression pasted into anything that runs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
