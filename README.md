# security-actions

Reusable GitHub composite actions for container image security in CI/CD pipelines. These actions cover vulnerability scanning, SBOM generation, keyless signing, and SBOM attestation. They are designed to be called from release workflows — primarily `sbe-devops/container-workflows` — and are public so any repository can reference them directly.

---

## Pipeline Overview

```
Build
  |
  v
Scan (pre-push)        — fail fast on HIGH/CRITICAL CVEs
  |
  v
SBOM (pre-push)        — generate bill of materials from local image
  |
  v
Push                   — push image to registry, capture digest
  |
  v
Sign (post-push)       — keyless sign the pushed digest via Sigstore
  |
  v
Attest (post-push)     — attach SBOM as a Cosign attestation to the digest
```

Scan and SBOM run against the local image before it is pushed. Sign and Attest require the immutable digest returned by the registry after push.

---

## Actions

| Action | Path | What it does | When it runs |
|--------|------|--------------|--------------|
| `scan` | `.github/actions/scan` | Trivy CVE scan; uploads SARIF to GitHub Security tab | Pre-push |
| `sbom` | `.github/actions/sbom` | Syft SBOM generation (CycloneDX, SPDX, or Syft JSON) | Pre-push |
| `sign` | `.github/actions/sign` | Cosign keyless image signing via Sigstore/Fulcio | Post-push |
| `attest` | `.github/actions/attest` | Cosign SBOM attestation attached to image digest | Post-push |

---

## Usage

Pin all references to a tag. Never use `@main`.

### scan

```yaml
- name: Scan image for CVEs
  uses: sbe-devops/security-actions/.github/actions/scan@v26.5.0
  with:
    image-ref: ${{ env.IMAGE_NAME }}:${{ env.IMAGE_TAG }}
    severity: HIGH,CRITICAL        # default
    exit-code: "1"                 # default — set "0" to report-only
    ignore-unfixed: "true"         # default
    sarif-file: trivy-results.sarif  # default
```

Requires `security-events: write` to upload SARIF.

### sbom

```yaml
- name: Generate SBOM
  id: sbom
  uses: sbe-devops/security-actions/.github/actions/sbom@v26.5.0
  with:
    image-ref: ${{ env.IMAGE_NAME }}:${{ env.IMAGE_TAG }}
    format: cyclonedx-json   # default — also: spdx-json, syft-json
    output-file: sbom.json   # default
```

Output `sbom-file` contains the path to the generated SBOM and can be passed to `attest`.

### sign

```yaml
- name: Sign image
  uses: sbe-devops/security-actions/.github/actions/sign@v26.5.0
  with:
    image-ref: ${{ env.IMAGE_URI }}@${{ steps.push.outputs.digest }}
```

`image-ref` must include the digest (`@sha256:...`). Requires `id-token: write`.

### attest

```yaml
- name: Attest SBOM
  uses: sbe-devops/security-actions/.github/actions/attest@v26.5.0
  with:
    image-ref: ${{ env.IMAGE_URI }}@${{ steps.push.outputs.digest }}
    sbom-file: ${{ steps.sbom.outputs.sbom-file }}
    sbom-type: cyclonedx   # default — also: spdx
```

`image-ref` must include the digest. Requires `id-token: write`.

---

## Permissions

Set these in the calling job's `permissions` block:

| Action | Required permission |
|--------|---------------------|
| `scan` | `security-events: write` |
| `sbom` | _(none beyond default)_ |
| `sign` | `id-token: write` |
| `attest` | `id-token: write` |

`sign` and `attest` use keyless signing via Sigstore/Fulcio. The OIDC token issued by GitHub Actions (`id-token: write`) is exchanged for a short-lived Fulcio certificate; no private key material is stored anywhere. The signing event is recorded in the Sigstore Rekor transparency log.

---

## Versioning

This repository follows CalVer: `vYY.M.N` (e.g. `v26.5.0`).

- Always pin to a specific tag — never `@main` or `@latest`.
- If a release fails validation, the tag is not reused; the next fix increments `N`.

---

## References

| Resource | Link |
|----------|------|
| Trivy documentation | https://aquasecurity.github.io/trivy/ |
| Syft / anchore-sbom-action | https://github.com/anchore/sbom-action |
| Cosign / Sigstore | https://docs.sigstore.dev/cosign/overview/ |
| Sigstore Fulcio (CA) | https://github.com/sigstore/fulcio |
| Sigstore Rekor (transparency log) | https://github.com/sigstore/rekor |
| CycloneDX specification | https://cyclonedx.org/specification/overview/ |
| SPDX specification | https://spdx.github.io/spdx-spec/ |
| SARIF specification | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html |
| OCI image specification | https://specs.opencontainers.org/image-spec/ |
