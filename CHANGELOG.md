# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
