#!/usr/bin/env python3
"""No `${{ }}` expression inside any `run:` block: workflows AND composite actions.

An expression in `run:` is pasted into the script's SOURCE before bash sees it, so a
caller's input becomes code. In sign/attest that ran beside the caller's OIDC token and
registry credentials (sweep, 2026-11-14). Every value reaches a script through `env:`.
Stricter than a list of contexts: ANY expression in run: is refused.

Run:  python3 tests/no-expr-in-run.py [file.yml ...]
      (default: .github/workflows/*.yml and .github/actions/*/action.yml)
"""
import re
import sys
from pathlib import Path

import yaml

EXPR = re.compile(r"\$\{\{(.*?)\}\}", re.S)


def steps_of(doc):
    for jname, job in (doc.get("jobs") or {}).items():
        for s in job.get("steps") or []:
            yield jname, s
    for s in ((doc.get("runs") or {}).get("steps") or []):
        yield "(composite)", s


def main(argv):
    root = Path(__file__).resolve().parent.parent / ".github"
    files = [Path(a) for a in argv] or sorted(root.glob("workflows/*.yml")) + sorted(root.glob("actions/*/action.yml"))
    total = 0
    for f in files:
        doc = yaml.safe_load(f.read_text()) or {}
        for j, s in steps_of(doc):
            run = s.get("run")
            if isinstance(run, str):
                for m in EXPR.finditer(run):
                    total += 1
                    print(f"  🔴 {f.parent.name}/{f.name}: {j!r} step {s.get('name')!r}: ${{{{ {m.group(1).strip()} }}}} inside run:")
    if total:
        print(f"{total} expression(s) inside run: across {len(files)} file(s). Pass each through env:.")
        return 1
    print(f"✓ no expression inside any run: block ({len(files)} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
