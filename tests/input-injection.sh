#!/usr/bin/env bash
# tests/input-injection.sh — sign's and attest's "Check inputs" on their own bytes.
#   every payload image-ref, sbom-type and sbom-file is refused, and none runs;
#   a real digest reference, a real SBOM file and each allowed type pass (controls);
#   CONTROL: v0.4.0's "Sign image", substituted the way GitHub substitutes ${{ }}, RUNS the
#   payload (skipped with a notice if v0.4.0 isn't in this clone).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; root="$here/.."
work="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/inj.XXXXXX")"; trap 'rm -rf -- "$work"' EXIT
fail=0
step() { python3 - "$1" "$2" "$3" <<'PY'
import sys, yaml
f, name, out = sys.argv[1:]
s = [s for s in (yaml.safe_load(open(f))["runs"]["steps"]) if s.get("name") == name]
assert len(s) == 1, f"{f}: no single step {name!r}"
open(out, "w").write(s[0]["run"])
PY
}
step "$root/.github/actions/sign/action.yml" "Check inputs" "$work/sign-check.sh" || exit 2
step "$root/.github/actions/attest/action.yml" "Check inputs" "$work/attest-check.sh" || exit 2
cd "$work" || exit 2
GOOD="112401921630.dkr.ecr.us-east-1.amazonaws.com/mcp-gateway@sha256:$(printf 'a%.0s' {1..64})"
echo '{"bomFormat":"CycloneDX"}' > sbom.json
# shellcheck disable=SC2016 # payloads, deliberately unexpanded
refs=('x@sha256:aa$(touch PWNED)' "$GOOD;touch PWNED" "$GOOD\`touch PWNED\`" "$GOOD && touch PWNED" \
      '112401921630.dkr.ecr.us-east-1.amazonaws.com/mcp-gateway:v1' "-$GOOD" "" $'x\n'"$GOOD")
for r in "${refs[@]}"; do
  for s in sign-check attest-check; do
    rm -f PWNED
    if IMAGE_REF="$r" SBOM_FILE=sbom.json SBOM_TYPE=cyclonedx bash "$s.sh" >/dev/null 2>&1 || [ -e PWNED ]; then
      echo "  🔴 $s accepted or ran image-ref ${r:0:40}"; fail=1
    else echo "  ✅ $s refused image-ref ${r:0:44}"; fi
  done
done
# shellcheck disable=SC2016
for t in 'cyclonedx$(touch PWNED)' 'slsaprovenance' '' 'cyclonedx; touch PWNED'; do
  rm -f PWNED
  if IMAGE_REF="$GOOD" SBOM_FILE=sbom.json SBOM_TYPE="$t" bash attest-check.sh >/dev/null 2>&1 || [ -e PWNED ]; then echo "  🔴 attest accepted sbom-type ${t:0:30}"; fail=1
  else echo "  ✅ attest refused sbom-type ${t:0:30}"; fi
done
ln -sf sbom.json link.json
# shellcheck disable=SC2016
for f in '--output=/etc/x' '' 'missing.json' 'link.json' 'sbom.json$(touch PWNED)'; do
  rm -f PWNED
  if IMAGE_REF="$GOOD" SBOM_FILE="$f" SBOM_TYPE=cyclonedx bash attest-check.sh >/dev/null 2>&1 || [ -e PWNED ]; then echo "  🔴 attest accepted sbom-file ${f:0:30}"; fail=1
  else echo "  ✅ attest refused sbom-file ${f:0:30}"; fi
done
for s in sign-check attest-check; do
  if IMAGE_REF="$GOOD" SBOM_FILE=sbom.json SBOM_TYPE=cyclonedx bash "$s.sh" >/dev/null 2>&1; then echo "  ✅ $s passes a digest reference (control)"; else echo "  🔴 $s refused a good reference"; fail=1; fi
done
for t in cyclonedx spdx spdxjson; do
  if IMAGE_REF="$GOOD" SBOM_FILE=sbom.json SBOM_TYPE=$t bash attest-check.sh >/dev/null 2>&1; then echo "  ✅ attest passes $t (control)"; else echo "  🔴 attest refused $t"; fail=1; fi
done
if git -C "$root" cat-file -e v0.4.0:.github/actions/sign/action.yml 2>/dev/null; then
  git -C "$root" show v0.4.0:.github/actions/sign/action.yml > old-sign.yml
  step old-sign.yml "Sign image" old.tpl
  python3 -c "
t=open('old.tpl').read().replace('\${{ inputs.image-ref }}','x\$(touch PWNED)')
open('old.sh','w').write('cosign() { :; }\n'+t)"
  rm -f PWNED; bash old.sh >/dev/null 2>&1
  if [ -e PWNED ]; then echo "  ✅ CONTROL: v0.4.0's Sign image ran the payload (the defect is real)"; else echo "  🔴 CONTROL: v0.4.0 did not run it; this test proves nothing"; fail=1; fi
else echo "  (control skipped: v0.4.0 not in this clone)"; fi
[ $fail -eq 0 ] || { echo "🔴 input-injection: FAILED"; exit 1; }
echo "input-injection: passed"
