#!/usr/bin/env bash
# tests/input-injection.sh — sign's and attest's "Check inputs" on their own bytes.
#   every payload image-ref, sbom-type and sbom-file is refused, and none runs;
#   a real digest reference, a real SBOM file and each allowed type pass (controls);
#   CONTROL: v0.4.0's "Sign image", substituted the way GitHub substitutes ${{ }}, RUNS the
#   payload (skipped with a notice if v0.4.0 isn't in this clone).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; root="$here/.."
work="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/inj.XXXXXX")"
outside="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/out.XXXXXX")"   # a dir the job did not make
ws="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/ws.XXXXXX")"         # stands in for GITHUB_WORKSPACE
trap 'rm -rf -- "$work" "$outside" "$ws" "${work}x"' EXIT
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
step "$root/.github/actions/scan/action.yml" "Check inputs" "$work/scan-check.sh" || exit 2
cd "$work" || exit 2
# The job's own dirs, as attest's confinement sees them. The real ones in CI are parents of
# $outside, so they are replaced, not inherited.
export RUNNER_TEMP="$work" GITHUB_WORKSPACE="$ws"
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
# sbom-file outside the job's dirs: a credential file, a `..` walk out, a symlinked dir that
# points out, and a sibling that only shares RUNNER_TEMP's prefix.
echo '{"auths":{}}' > "$outside/config.json"
mkdir -p "${work}x" && echo '{}' > "${work}x/config.json"
ln -sfn "$outside" lnkdir
escapes=("$outside/config.json" "$work/../$(basename "$outside")/config.json" "lnkdir/config.json" "${work}x/config.json")
labels=("a file outside both dirs" "a .. walk out of RUNNER_TEMP" "a symlinked dir pointing out" "a sibling sharing RUNNER_TEMP's prefix")
check_escapes() { # check_escapes <script> <want: refused|accepted>
  local i n=0
  for i in "${!escapes[@]}"; do
    if IMAGE_REF="$GOOD" SBOM_FILE="${escapes[$i]}" SBOM_TYPE=cyclonedx bash "$1" >/dev/null 2>&1; then
      if [ "$2" = accepted ]; then n=$((n+1)); else echo "  🔴 attest accepted sbom-file: ${labels[$i]}"; fail=1; fi
    else
      [ "$2" = refused ] && echo "  ✅ attest refused sbom-file: ${labels[$i]}" || true
    fi
  done
  [ "$2" = refused ] || echo "$n"
}
check_escapes attest-check.sh refused
if RUNNER_TEMP="" GITHUB_WORKSPACE="" IMAGE_REF="$GOOD" SBOM_FILE=sbom.json SBOM_TYPE=cyclonedx bash attest-check.sh >/dev/null 2>&1; then
  echo "  🔴 attest accepted sbom-file with neither RUNNER_TEMP nor GITHUB_WORKSPACE set"; fail=1
else echo "  ✅ attest refused sbom-file with neither RUNNER_TEMP nor GITHUB_WORKSPACE set"; fi
echo '{"bomFormat":"CycloneDX"}' > "$ws/sbom.json"
for f in "$work/sbom.json" "$ws/sbom.json" "sbom.json"; do
  if IMAGE_REF="$GOOD" SBOM_FILE="$f" SBOM_TYPE=cyclonedx bash attest-check.sh >/dev/null 2>&1; then g="${f/#$work/RUNNER_TEMP}"; echo "  ✅ attest passes sbom-file ${g/#$ws/GITHUB_WORKSPACE} (control)"
  else echo "  🔴 attest refused sbom-file $f"; fail=1; fi
done
# MUTANT: the same check with the confinement's refusal removed must accept every escape, or
# the cases above are passing for some other reason.
# shellcheck disable=SC2016 # sed patterns, deliberately unexpanded
sed 's/if \[ "\$inside" != true \]; then/if false; then/' attest-check.sh > attest-mut.sh
if cmp -s attest-check.sh attest-mut.sh; then echo "  🔴 MUTANT: the confinement anchor didn't apply"; fail=1
else
  got="$(check_escapes attest-mut.sh accepted)"
  if [ "$got" = "${#escapes[@]}" ]; then echo "  ✅ MUTANT: without the confinement, all ${#escapes[@]} escapes are accepted (the cases are load-bearing)"
  else echo "  🔴 MUTANT: without the confinement, only $got of ${#escapes[@]} escapes are accepted"; fail=1; fi
fi
# scan's trivy-version: only X.Y.Z reaches trivy-action.
# shellcheck disable=SC2016
vers=('latest' 'v0.70.0' '0.70' '0.70.0.1' '' '0.70.0$(touch PWNED)' '0.70.0; touch PWNED' $'0.70.0\n' '../../0.70.0' '0.70.*')
for v in "${vers[@]}"; do
  rm -f PWNED
  if TRIVY_VERSION="$v" bash scan-check.sh >/dev/null 2>&1 || [ -e PWNED ]; then echo "  🔴 scan accepted trivy-version ${v:0:30}"; fail=1
  else echo "  ✅ scan refused trivy-version ${v:0:30}"; fi
done
for v in 0.70.0 0.69.3 1.0.0; do
  if TRIVY_VERSION="$v" bash scan-check.sh >/dev/null 2>&1; then echo "  ✅ scan passes trivy-version $v (control)"; else echo "  🔴 scan refused trivy-version $v"; fail=1; fi
done
# MUTANT: with the shape check removed, the payloads pass.
# shellcheck disable=SC2016 # sed patterns, deliberately unexpanded
sed 's/if ! \[\[ "\$TRIVY_VERSION" =~/if false \&\& [[ "$TRIVY_VERSION" =~/' scan-check.sh > scan-mut.sh
if cmp -s scan-check.sh scan-mut.sh; then echo "  🔴 MUTANT: the trivy-version anchor didn't apply"; fail=1
else
  n=0; for v in "${vers[@]}"; do TRIVY_VERSION="$v" bash scan-mut.sh >/dev/null 2>&1 && n=$((n+1)); done
  if [ "$n" = "${#vers[@]}" ]; then echo "  ✅ MUTANT: without the shape check, all ${#vers[@]} bad versions pass (the cases are load-bearing)"
  else echo "  🔴 MUTANT: without the shape check, only $n of ${#vers[@]} pass"; fail=1; fi
fi
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
