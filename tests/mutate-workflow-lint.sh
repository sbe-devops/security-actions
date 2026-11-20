#!/usr/bin/env bash
# tests/mutate-workflow-lint.sh ZIZMOR ACTIONLINT — each mutant switches off one part of
# lint.py; tests/workflow-lint.sh must then FAIL (a mutant that survives is a part nothing tests).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$here/../.github/actions/workflow-lint/lint.py"
Z="${1:?}"; A="${2:?}"
backup="$(mktemp "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/lint.py.XXXXXX")"; cp "$src" "$backup"
trap 'cp "$backup" "$src"; rm -f "$backup"' EXIT
survived=0
mutant() {  # mutant <label> <python: old> <python: new>
  cp "$backup" "$src"
  python3 - "$src" "$2" "$3" <<'PY' || { echo "  🔴 $1: ANCHOR MISS (the mutant did not apply)"; survived=1; return; }
import sys
p, old, new = (a.replace("\\n", "\n") for a in sys.argv[1:])
t = open(p).read()
assert t.count(old) == 1, f"anchor count {t.count(old)}"
open(p, "w").write(t.replace(old, new))
PY
  if bash "$here/workflow-lint.sh" "$Z" "$A" >/dev/null 2>&1; then echo "  🔴 $1: SURVIVED"; survived=1; else echo "  ✅ $1: killed"; fi
}
mutant "default persona (taint cut)"   '"--persona=pedantic", '            ''
mutant "severity cut raised to low"     '"--min-severity=informational",'   '"--min-severity=low",'
mutant "repo config read"              '"--no-config", '                   ''
mutant "blanket-config check off"      'if p.is_file() and "template-injection" in p.read_text():' 'if False:'
mutant "reason not required"           'if REASON.match(m.group(2)):'      'if True:'
mutant "zizmor ignored"                'if x.get("ident") != "template-injection":' 'if True:'
mutant "zizmor failure = pass"         'return [f"zizmor did not produce a report' 'return []  # [f"zizmor did not produce a report'
mutant "actionlint ignored"            'for e in errs if e.get("kind") == "expression" and' 'for e in errs if False and'
mutant "literal-type filter off"       'and not LITERAL_INPUT_TYPE.match(e.get("message", ""))]' ']'
mutant "literal-type filter takes all" 'and not LITERAL_INPUT_TYPE.match(e.get("message", ""))]' 'and False]'
mutant "container options unchecked"   'if isinstance(c, dict) and EXPR.search(str(c.get("options", ""))):' 'if False:'
mutant "docker args unchecked"         'if EXPR.search(str(w.get(k, ""))):' 'if False:'
mutant "composite actions skipped"     'files = wf + actions'               'files = wf'
mutant "no-files passes"               'if not files:\n        print("::error::workflow-lint found no' 'if False:\n        print("::error::workflow-lint found no'
mutant "actionlint repo config read"  '"-config-file", cfg.name, ' ''
mutant "unparseable file passes"       'except yaml.YAMLError as e:\n            out.append' 'except yaml.YAMLError as e:\n            pass  # out.append'
[ $survived -eq 0 ] || { echo "🔴 mutate-workflow-lint: a mutant survived"; exit 1; }
echo "mutate-workflow-lint: all mutants killed"
