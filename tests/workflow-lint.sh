#!/usr/bin/env bash
# tests/workflow-lint.sh ZIZMOR ACTIONLINT — the workflow-lint gate against its fixtures.
# Each tests/workflow-lint/<case>/ is a repo root. pass-* must pass. fail-* must FAIL and name the
# reason this table expects (so a fixture can't "fail" for some unrelated cause and count).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
lint="$here/../.github/actions/workflow-lint/lint.py"
Z="${1:?usage: workflow-lint.sh ZIZMOR ACTIONLINT}"; A="${2:?usage: workflow-lint.sh ZIZMOR ACTIONLINT}"
reason() {
  case "$1" in
    fail-custom-shell)                      echo "actionlint [expression]" ;;
    # the custom-shell finding must still appear, which it only does if the repo's
    # actionlint.yaml (ignore everything) was NOT read
    fail-actionlint-config-ignore)          echo "actionlint [expression]" ;;
    fail-docker-args|fail-docker-entrypoint) echo "docker:// with." ;;
    fail-container-options|fail-services-options) echo ".options holds an expression" ;;
    fail-blanket-config-ignore)             echo "blanket ignores are refused" ;;
    fail-ignore-without-reason)             echo "without a written reason" ;;
    fail-no-files)                          echo "found no workflow or action file" ;;
    fail-unparseable-only)                  echo "zizmor did not produce a report" ;;
    fail-unparseable-mixed)                 echo "could not parse as YAML" ;;
    # with-hit: the zizmor finding must appear, which it only does if the repo config was NOT read
    fail-blanket-config-with-hit)           echo "template-injection (" ;;
    fail-*)                                 echo "template-injection" ;;
  esac
}
# Each fixture runs as ITS OWN git repository root, in a copy: zizmor and actionlint both find
# a repo's config at the git root, so a fixture nested in this repo would never have its
# zizmor.yml or actionlint.yaml read, and the config-refusal cases would prove nothing.
work="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/wl.XXXXXX")"; trap 'rm -rf -- "$work"' EXIT
bad=0; n=0
for src in "$here"/workflow-lint/*/; do
  c="$(basename "$src")"; n=$((n + 1))
  d="$work/$c"; cp -R "$src" "$d"; git -C "$d" init -q
  # Fixture actions are stored as action.fixture.yml, so this repo's own gate doesn't lint them
  # as real actions; in the copy they become action.yml.
  while IFS= read -r f; do mv "$f" "${f%action.fixture.yml}action.yml"; done < <(find "$d" -name action.fixture.yml)
  out="$(python3 "$lint" --root "$d" --zizmor "$Z" --actionlint "$A" 2>&1)"; rc=$?
  case "$c" in
    pass-*)
      if [ $rc -eq 0 ]; then echo "  ✅ $c: passes"; else echo "  🔴 $c: should pass"; printf "%s\n" "$out"; bad=1; fi
      if [ "$c" = pass-ignore-with-reason ] && ! grep -q "reviewed exception:" <<<"$out"; then echo "  🔴 $c: the exception was not listed for review"; bad=1; fi ;;
    fail-*)
      want="$(reason "$c")"
      if [ $rc -eq 0 ]; then echo "  🔴 $c: PASSED (should fail on: $want)"; bad=1
      elif ! grep -qF -- "$want" <<<"$out"; then echo "  🔴 $c: failed, but not on '$want'"; printf "%s\n" "$out"; bad=1
      else echo "  ✅ $c: fails on $want"; fi ;;
  esac
done
[ "$n" -ge 20 ] || { echo "🔴 only $n fixtures found"; bad=1; }
[ $bad -eq 0 ] || { echo "🔴 workflow-lint fixtures: FAILED"; exit 1; }
echo "workflow-lint fixtures: $n passed"
