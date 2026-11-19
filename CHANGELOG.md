# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **`workflow-lint`: the gate that no `${{ }}` expression is pasted into anything that runs,**
  whoever controls it (ORCA ruling 2026-11-14, after GITOPS's zizmor/actionlint evaluation,
  corp `dc42e3a`).
  - **How:** zizmor 1.32.0 `template-injection` at every severity (pedantic persona, hash-pinned
    install, `--no-config`), actionlint 1.7.12 `[expression]` (its own empty config), and a check
    for `container`/`services` `options`, `docker://` args and unparseable files.
  - **Exceptions:** per-line `-- reason:` ignores only. Blanket configs are refused.
  - **Tests:** 26 fixtures and 14 mutants. This repo's own CI now runs it, which retires
    `tests/no-expr-in-run.py`.

### Security

- **`sign` and `attest` pasted their inputs into `run:`** (`${{ inputs.image-ref }}`, `sbom-file`, `sbom-type`).
  - **The effect:** a caller's value became script source, in the caller's push job, beside its OIDC token and registry credentials. Found by GITOPS's sweep after PROOF's container-workflows finding (corp `1a99223`).
  - **Now:**
    - every input reaches its script through `env:`, quoted;
    - a first **Check inputs** step, before cosign is installed, refuses an `image-ref` that isn't `<registry>/<repository>@sha256:<64 hex>`, an `sbom-type` outside `cyclonedx|spdx|spdxjson`, and an `sbom-file` that's empty, option-like, missing or a symlink.
  - **⚠️ Behaviour change:** `image-ref` must be a **digest** reference. A tag is refused. docker-release already passes `<repo>@<digest>`.
  - **Tests:**
    - `tests/no-expr-in-run.py` (workflows and composite actions; 7 at v0.4.0, 0 now);
    - `tests/input-injection.sh` (payloads refused and none run, controls pass, and v0.4.0's step runs one).

---

## [v0.3.0] - 2026-05-07

### Changed

- `scan` action: replaced `aquasecurity/trivy-action` with a direct Trivy binary install,
  eliminating GitHub Actions API telemetry calls made by the third-party action wrapper.

---

## [v0.2.0] - 2026-05-07

### Changed

- `scan` action: simplified to table output only; removed SARIF upload step and the
  `security-events: write` dependency that came with it.

---

## [v0.1.0] - 2026-05-07

### Added

- Initial release: `scan`, `sbom`, `sign`, and `attest` composite actions.
  - `scan` — Trivy CVE scan with configurable severity and exit-code.
  - `sbom` — Syft SBOM generation in CycloneDX, SPDX, or Syft JSON format.
  - `sign` — Cosign keyless image signing via Sigstore/Fulcio.
  - `attest` — Cosign SBOM attestation attached to the image digest.
