from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.platypus.flowables import CondPageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUTPUT = "/Users/emo/git/sbe-devops/security-actions/docs/SBE_Container_Security_Hardening.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    rightMargin=0.85*inch,
    leftMargin=0.85*inch,
    topMargin=0.9*inch,
    bottomMargin=0.9*inch,
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
    fontSize=22, textColor=colors.HexColor('#1a1a2e'), spaceAfter=4)
subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
    fontSize=11, textColor=colors.HexColor('#555555'), spaceAfter=2)
section_header_style = ParagraphStyle('SectionHeader', parent=styles['Normal'],
    fontSize=13, fontName='Helvetica-Bold', textColor=colors.white,
    spaceAfter=6, spaceBefore=6, leftIndent=8)
heading_style = ParagraphStyle('Heading', parent=styles['Normal'],
    fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a2e'),
    spaceAfter=6, spaceBefore=10)
subheading_style = ParagraphStyle('SubHeading', parent=styles['Normal'],
    fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a4a8a'),
    spaceAfter=4, spaceBefore=8)
body_style = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=10, textColor=colors.HexColor('#333333'), spaceAfter=4, leading=14)
bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'],
    fontSize=10, textColor=colors.HexColor('#333333'), leading=14,
    leftIndent=16, spaceAfter=3)
footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
    fontSize=8, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
callout_style = ParagraphStyle('Callout', parent=styles['Normal'],
    fontSize=10, textColor=colors.HexColor('#1a4a00'), leading=14)
note_style = ParagraphStyle('Note', parent=styles['Normal'],
    fontSize=10, textColor=colors.HexColor('#7b2d00'), leading=14)
label_style = ParagraphStyle('Label', parent=styles['Normal'],
    fontSize=9.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#444444'), leading=13)
code_style = ParagraphStyle('Code', parent=styles['Normal'],
    fontSize=8.5, fontName='Courier', textColor=colors.HexColor('#1a1a2e'),
    leading=13, leftIndent=12)

th_white = ParagraphStyle('ThWhite', parent=styles['Normal'],
    fontSize=9.5, fontName='Helvetica-Bold', textColor=colors.white, leading=13)
td_bold_blue = ParagraphStyle('TdBoldBlue', parent=styles['Normal'],
    fontSize=9.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a4a8a'), leading=13)
td_bold_green = ParagraphStyle('TdBoldGreen', parent=styles['Normal'],
    fontSize=9.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a4a00'), leading=13)
td_normal = ParagraphStyle('TdNormal', parent=styles['Normal'],
    fontSize=9.5, textColor=colors.HexColor('#333333'), leading=13)
td_code = ParagraphStyle('TdCode', parent=styles['Normal'],
    fontSize=8.5, fontName='Courier', textColor=colors.HexColor('#1a1a2e'), leading=13)

DARK_NAVY   = colors.HexColor('#1a1a2e')
DARK_BLUE   = colors.HexColor('#1a4a8a')
DARK_GREEN  = colors.HexColor('#1a4a00')
MID_BLUE    = colors.HexColor('#2c6fad')
LIGHT_GREEN = colors.HexColor('#e8f5e9')
LIGHT_BLUE  = colors.HexColor('#e8f0fb')
LIGHT_GREY  = colors.HexColor('#f5f5f5')
LIGHT_RED   = colors.HexColor('#fdf0ed')
MID_GREY    = colors.HexColor('#dddddd')
BORDER_GREY = colors.HexColor('#cccccc')

def section_banner(text, bg=DARK_NAVY):
    table = Table([[Paragraph(text, section_header_style)]], colWidths=[6.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    return table

def callout_box(text, bg=LIGHT_GREEN, style=None):
    s = style or callout_style
    table = Table([[Paragraph(text, s)]], colWidths=[6.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_GREY),
    ]))
    return table

def std_table(headers, rows, col_widths, header_bg=DARK_NAVY):
    header_row = [Paragraph(h, th_white) for h in headers]
    data = [header_row]
    for row in rows:
        data.append([Paragraph(str(c[0]), c[1]) if isinstance(c, tuple) else Paragraph(str(c), td_normal) for c in row])
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), header_bg),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ('GRID', (0,0), (-1,-1), 0.4, BORDER_GREY),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return table

story = []

# ── Cover ─────────────────────────────────────────────────────────────────────

story.append(Spacer(1, 0.6*inch))
story.append(Paragraph("SBE DevOps", subtitle_style))
story.append(Paragraph("Container Security Hardening", title_style))
story.append(Paragraph("Architecture, Tooling, and Audit Trail", subtitle_style))
story.append(Spacer(1, 0.1*inch))
story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_NAVY))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("Version 1.0  |  May 2026  |  sbe-devops/security-actions", footer_style))
story.append(Spacer(1, 0.4*inch))

story.append(callout_box(
    "This document describes the container security controls built into SBE DevOps CI/CD pipelines. "
    "Every container image released from an SBE project passes through a defined security gate before "
    "reaching production. The components, rationale, and audit evidence produced are documented here "
    "for internal reference and external audit.",
    bg=LIGHT_BLUE, style=body_style
))
story.append(Spacer(1, 0.25*inch))

# ── Section 1: Philosophy ─────────────────────────────────────────────────────

story.append(section_banner("1. Security Philosophy"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("Shift Left, Gate Right", heading_style))
story.append(Paragraph(
    "Security is applied at every stage of the container lifecycle — not bolted on after the fact. "
    "Vulnerabilities are caught before images reach any registry. SBOMs are generated before push. "
    "Images are signed and attested after push so consumers can cryptographically verify provenance. "
    "No image enters production without passing all gates.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Core Principles", subheading_style))
bullets = [
    "<b>No secrets in images</b> — credentials are injected at runtime via AWS SSM, never baked in.",
    "<b>Non-root by default</b> — all images run as UID 1001 (appuser), never root.",
    "<b>Immutable releases</b> — ECR repositories use IMMUTABLE_WITH_EXCLUSION; released tags cannot be overwritten.",
    "<b>Fail on CRITICAL CVEs</b> — builds fail before push if HIGH or CRITICAL vulnerabilities are found.",
    "<b>Verifiable provenance</b> — every released image is signed by digest and carries an attested SBOM.",
    "<b>Arm64 only</b> — Graviton reduces attack surface by eliminating x86-specific exploit vectors.",
]
for b in bullets:
    story.append(Paragraph(f"&#8226;  {b}", bullet_style))
story.append(Spacer(1, 0.2*inch))

# ── Section 2: Pipeline Architecture ─────────────────────────────────────────

story.append(CondPageBreak(2.5*inch))
story.append(section_banner("2. Pipeline Architecture"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "The security pipeline is embedded in the container release workflow "
    "(sbe-devops/container-workflows). Security actions are sourced from "
    "sbe-devops/security-actions and versioned independently.",
    body_style))
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph("Release Pipeline Flow", subheading_style))
pipeline_rows = [
    [("Stage", td_bold_blue), ("Action", td_bold_blue), ("Runs On", td_bold_blue), ("Blocks Push?", td_bold_blue)],
    ["1. Build", "docker/build-push-action (load)", "Local daemon (TEST_IMAGE)", "N/A"],
    ["2. Version Extract", "docker run --entrypoint ''", "TEST_IMAGE", "Yes — fails if no semver"],
    ["3. CVE Scan", "security-actions/scan (Trivy)", "TEST_IMAGE", "Yes — fails on HIGH/CRITICAL"],
    ["4. SBOM Generation", "security-actions/sbom (Syft)", "TEST_IMAGE", "No — generates artifact"],
    ["5. Structure Tests", "container-structure-test", "TEST_IMAGE", "Yes — fails on test error"],
    ["6. Push to ECR", "docker/build-push-action (push)", "ECR registry", "N/A"],
    ["7. Sign Image", "security-actions/sign (Cosign)", "ECR image by digest", "No — post-push"],
    ["8. Attest SBOM", "security-actions/attest (Cosign)", "ECR image by digest", "No — post-push"],
]
header_row = pipeline_rows[0]
data_rows = []
for row in pipeline_rows[1:]:
    data_rows.append([(c, td_normal) if isinstance(c, str) else c for c in row])

table_data = [[Paragraph(h[0], th_white) for h in header_row]]
for row in data_rows:
    table_data.append([Paragraph(c[0], c[1]) for c in row])

pipeline_table = Table(table_data, colWidths=[1.3*inch, 2.0*inch, 1.9*inch, 1.6*inch])
pipeline_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), DARK_NAVY),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
    ('GRID', (0,0), (-1,-1), 0.4, BORDER_GREY),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING', (0,0), (-1,-1), 8),
    ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
story.append(pipeline_table)
story.append(Spacer(1, 0.2*inch))

story.append(callout_box(
    "Stages 1-5 run against the locally loaded TEST_IMAGE — no vulnerable image ever touches ECR. "
    "Stages 7-8 run post-push using the immutable image digest, ensuring the signature and attestation "
    "reference exactly what was pushed.",
    bg=LIGHT_GREEN, style=callout_style
))
story.append(Spacer(1, 0.2*inch))

# ── Section 3: CVE Scanning ───────────────────────────────────────────────────

story.append(PageBreak())
story.append(section_banner("3. CVE Scanning — Trivy"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Trivy (by Aqua Security) is an open-source vulnerability scanner. It scans the container image "
    "filesystem and package manifests against the OSV, NVD, and OS-vendor advisory databases.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("What Trivy Scans", subheading_style))
scan_targets = [
    ("OS packages", "RPM (Amazon Linux), DEB, APK — checks installed versions against CVE databases."),
    ("Language packages", "Python (pip), Node (npm), Go modules, Java (Maven/Gradle), Ruby (gems)."),
    ("Secrets", "Detects accidentally embedded API keys, tokens, and credentials."),
    ("Misconfigurations", "Dockerfile best practice violations (optional, not enabled by default)."),
]
for target, desc in scan_targets:
    story.append(Paragraph(f"<b>{target}</b> — {desc}", bullet_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Configuration", subheading_style))
config_rows = [
    [("Input", td_bold_blue), ("Setting", td_bold_blue), ("Rationale", td_bold_blue)],
    ["Severity threshold", "HIGH, CRITICAL", "LOW/MEDIUM are noise in base images; actionable findings only"],
    ["Exit code", "1 (fail build)", "Vulnerable images never reach ECR"],
    ["ignore-unfixed", "true", "Eliminates CVEs with no available fix — reduces alert fatigue"],
    ["Output format", "SARIF", "Uploaded to GitHub Security tab for visibility and tracking"],
    ["Scan target", "TEST_IMAGE (local)", "Scanned before push — registry stays clean"],
]
story.append(std_table(
    ["Input", "Setting", "Rationale"],
    [[(c, td_normal) if isinstance(c, str) else c for c in row] for row in config_rows[1:]],
    [1.5*inch, 1.8*inch, 3.5*inch]
))
story.append(Spacer(1, 0.15*inch))

story.append(Paragraph("SARIF Output", subheading_style))
story.append(Paragraph(
    "Trivy results are written in SARIF (Static Analysis Results Interchange Format) and uploaded "
    "to the GitHub Security tab via codeql-action/upload-sarif. This provides a persistent, "
    "searchable audit trail of every scan result — including historical findings — visible to all "
    "repo contributors with Security permission.",
    body_style))
story.append(Spacer(1, 0.2*inch))

# ── Section 4: SBOM ───────────────────────────────────────────────────────────

story.append(CondPageBreak(3*inch))
story.append(section_banner("4. Software Bill of Materials — Syft"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "A Software Bill of Materials (SBOM) is a machine-readable inventory of every software component "
    "in a container image — OS packages, language libraries, and their versions. Syft (by Anchore) "
    "generates the SBOM from the built image before push.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Why SBOMs Matter", subheading_style))
reasons = [
    "Incident response — when a new CVE drops (e.g. Log4Shell), you can immediately query which images are affected without re-scanning everything.",
    "Compliance — US Executive Order 14028 (2021) mandates SBOMs for software sold to federal agencies. Ahead of the curve.",
    "Supply chain visibility — shows exactly what third-party code is running in production, including transitive dependencies.",
    "Audit trail — SBOM attested to the image digest proves the image content has not changed since the SBOM was generated.",
]
for r in reasons:
    story.append(Paragraph(f"&#8226;  {r}", bullet_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Format", subheading_style))
story.append(Paragraph(
    "SBOMs are generated in <b>CycloneDX JSON</b> format — the OWASP-maintained standard designed "
    "specifically for security use cases. CycloneDX is the format required by most compliance "
    "frameworks and supported natively by Trivy, Grype, and major SCA tools. SPDX JSON is also "
    "available as an option.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(callout_box(
    "The SBOM is generated from the local TEST_IMAGE before push, then attached as a Cosign "
    "attestation to the pushed image by digest. Anyone who pulls the image can verify and retrieve "
    "the SBOM using: cosign download attestation <image>@<digest>",
    bg=LIGHT_BLUE, style=body_style
))
story.append(Spacer(1, 0.2*inch))

# ── Section 5: Image Signing ──────────────────────────────────────────────────

story.append(PageBreak())
story.append(section_banner("5. Image Signing — Cosign + Sigstore"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Container images are signed using Cosign with keyless signing via the Sigstore public "
    "infrastructure. Keyless signing eliminates the operational overhead of managing long-lived "
    "signing keys — the identity proof comes from the GitHub Actions OIDC token.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("How Keyless Signing Works", subheading_style))
steps = [
    ("1. OIDC token", "GitHub Actions provides a short-lived OIDC token proving the workflow identity (e.g. sbe-devops/csi-python, release workflow, main branch)."),
    ("2. Fulcio CA", "Sigstore's Fulcio certificate authority exchanges the OIDC token for a short-lived X.509 signing certificate tied to the workflow identity."),
    ("3. Sign by digest", "Cosign signs the image digest (sha256:...) using the ephemeral certificate. The signature is pushed to the ECR repository as an OCI artifact."),
    ("4. Rekor log", "The signing event is recorded in Sigstore's Rekor transparency log — a tamper-evident, append-only ledger. The log entry is publicly auditable."),
    ("5. Certificate expires", "The signing certificate expires in minutes. No long-lived key exists to be stolen or rotated."),
]
for step, desc in steps:
    story.append(Paragraph(f"<b>{step}</b> — {desc}", bullet_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Verification", subheading_style))
story.append(Paragraph("Anyone with Cosign installed can verify a signed image:", body_style))
story.append(Paragraph(
    "cosign verify --certificate-identity-regexp 'https://github.com/sbe-devops/.*' "
    "--certificate-oidc-issuer 'https://token.actions.githubusercontent.com' "
    "&lt;image&gt;@&lt;digest&gt;",
    code_style))
story.append(Spacer(1, 0.1*inch))
story.append(callout_box(
    "Signing is by digest, not by tag. Tags are mutable; digests are not. A valid signature on a "
    "digest proves the exact image bytes were produced by our pipeline — not just something with "
    "the same tag name.",
    bg=LIGHT_GREEN, style=callout_style
))
story.append(Spacer(1, 0.2*inch))

# ── Section 6: SBOM Attestation ───────────────────────────────────────────────

story.append(CondPageBreak(3*inch))
story.append(section_banner("6. SBOM Attestation — Cosign Attest"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Attestation binds the SBOM to the image digest using the same Sigstore infrastructure as "
    "image signing. The SBOM is stored as an OCI artifact in ECR alongside the image, retrievable "
    "by anyone with pull access.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("Attestation vs. Signing", subheading_style))
story.append(std_table(
    ["", "Image Signing", "SBOM Attestation"],
    [
        [("What it proves", td_bold_blue), "Image bytes are authentic and pipeline-produced", "SBOM accurately describes the image contents at release time"],
        [("What is signed", td_bold_blue), "The image digest", "The SBOM + image digest together"],
        [("Storage", td_bold_blue), "OCI artifact in ECR alongside the image", "OCI artifact in ECR alongside the image"],
        [("Retrieval", td_bold_blue), "cosign verify <image>@<digest>", "cosign download attestation <image>@<digest>"],
    ],
    [1.4*inch, 2.7*inch, 2.7*inch]
))
story.append(Spacer(1, 0.2*inch))

# ── Section 7: Tooling Reference ─────────────────────────────────────────────

story.append(PageBreak())
story.append(section_banner("7. Tooling Reference"))
story.append(Spacer(1, 0.1*inch))

story.append(std_table(
    ["Tool", "Version Pinned", "Purpose", "Maintained By"],
    [
        [("Trivy", td_bold_blue), "aquasecurity/trivy-action@v0.36.0", "CVE scanning, SARIF output", "Aqua Security"],
        [("Syft", td_bold_blue), "anchore/sbom-action@v0", "SBOM generation (CycloneDX/SPDX)", "Anchore"],
        [("Cosign", td_bold_blue), "sigstore/cosign-installer@v3", "Image signing + SBOM attestation", "Sigstore / OpenSSF"],
        [("CodeQL Upload", td_bold_blue), "codeql-action/upload-sarif@v4", "SARIF -> GitHub Security tab", "GitHub"],
        [("container-structure-test", td_bold_blue), "v1.22.1 (binary)", "Image structure validation", "Google"],
        [("Fulcio CA", td_bold_blue), "Public Sigstore instance", "Short-lived signing certificates", "Sigstore / Linux Foundation"],
        [("Rekor", td_bold_blue), "Public Sigstore instance", "Signing transparency log", "Sigstore / Linux Foundation"],
    ],
    [1.2*inch, 2.2*inch, 2.2*inch, 1.2*inch]
))
story.append(Spacer(1, 0.2*inch))

# ── Section 8: Audit Trail ────────────────────────────────────────────────────

story.append(CondPageBreak(3*inch))
story.append(section_banner("8. Audit Trail — What Every Release Produces"))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Every image released through the SBE container pipeline produces a complete, verifiable audit "
    "trail. The following artifacts are available for any released image.",
    body_style))
story.append(Spacer(1, 0.1*inch))

story.append(std_table(
    ["Artifact", "Where It Lives", "What It Proves"],
    [
        [("SARIF scan report", td_bold_blue), "GitHub Security tab (repo)", "CVE state at build time — findings, severity, fix availability"],
        [("SBOM (CycloneDX JSON)", td_bold_blue), "ECR — OCI artifact on image digest", "Complete component inventory at release time"],
        [("Cosign signature", td_bold_blue), "ECR — OCI artifact on image digest", "Image bytes produced by our GitHub Actions pipeline"],
        [("SBOM attestation", td_bold_blue), "ECR — OCI artifact on image digest", "SBOM is bound to this exact image digest"],
        [("Rekor log entry", td_bold_blue), "Sigstore public transparency log", "Tamper-evident record of signing event, timestamp, identity"],
        [("GHA workflow run", td_bold_blue), "GitHub Actions run history", "Full pipeline execution log, steps, inputs, runner"],
        [("Build metadata file", td_bold_blue), "Baked into image at /usr/libexec/*/build", "Runtime + calver tag visible in container stdout at startup"],
    ],
    [1.6*inch, 2.3*inch, 2.9*inch]
))
story.append(Spacer(1, 0.2*inch))

story.append(callout_box(
    "To retrieve all security artifacts for a released image:\n"
    "  cosign verify <image>@<digest>                         # verify signature\n"
    "  cosign download attestation <image>@<digest>           # retrieve SBOM\n"
    "  cosign verify-attestation --type cyclonedx <image>@<digest>  # verify + decode SBOM",
    bg=LIGHT_GREY, style=code_style
))
story.append(Spacer(1, 0.2*inch))

# ── Section 9: References ─────────────────────────────────────────────────────

story.append(PageBreak())
story.append(section_banner("9. References"))
story.append(Spacer(1, 0.1*inch))

story.append(std_table(
    ["Resource", "URL"],
    [
        [("Trivy documentation", td_bold_blue), "https://aquasecurity.github.io/trivy/"],
        [("Trivy GitHub Action", td_bold_blue), "https://github.com/aquasecurity/trivy-action"],
        [("Syft SBOM generator", td_bold_blue), "https://github.com/anchore/syft"],
        [("anchore/sbom-action", td_bold_blue), "https://github.com/anchore/sbom-action"],
        [("Cosign", td_bold_blue), "https://github.com/sigstore/cosign"],
        [("Sigstore project", td_bold_blue), "https://www.sigstore.dev"],
        [("Fulcio CA", td_bold_blue), "https://github.com/sigstore/fulcio"],
        [("Rekor transparency log", td_bold_blue), "https://github.com/sigstore/rekor"],
        [("CycloneDX specification", td_bold_blue), "https://cyclonedx.org/specification/overview/"],
        [("SPDX specification", td_bold_blue), "https://spdx.dev/specifications/"],
        [("SARIF specification", td_bold_blue), "https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning"],
        [("OCI image spec (CNCF)", td_bold_blue), "https://github.com/opencontainers/image-spec"],
        [("OpenSSF Scorecard", td_bold_blue), "https://securityscorecards.dev"],
        [("US EO 14028 — SBOM mandate", td_bold_blue), "https://www.cisa.gov/sbom"],
        [("NIST SP 800-190 — Container Security", td_bold_blue), "https://csrc.nist.gov/publications/detail/sp/800-190/final"],
    ],
    [2.2*inch, 4.6*inch]
))

story.append(Spacer(1, 0.3*inch))
story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GREY))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("SBE DevOps  |  sbe-devops/security-actions  |  v1.0  |  May 2026", footer_style))

doc.build(story)
print(f"Generated: {OUTPUT}")
