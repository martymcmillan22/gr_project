# BTPE Document Classification Policy

Policy ID: BTPE-SEC-DOC-001
Version: v0.1
Effective Date: [YYYY-MM-DD]
Applies To: All BTPE materials (documents, code, prompts, datasets, exports, screenshots)

## 1. Classification Levels

### 1. Restricted
Definition:
- Highest sensitivity; disclosure can materially harm BTPE IP position or business value.

Examples:
- Full generation rule engine logic
- Complete tier mapping corpora
- Proprietary pattern transformation details
- High-value prompt libraries and model tuning assets

Handling:
- Private storage only
- Least-privilege access
- No external sharing without written executive/legal approval + NDA
- Mandatory watermark/tag: "BTPE RESTRICTED"

### 2. Confidential
Definition:
- Sensitive internal information not intended for public release.

Examples:
- Internal architecture docs
- Non-public roadmap and experiments
- Internal evaluation results

Handling:
- Internal sharing on need-to-know basis
- External sharing only under signed NDA
- Tag: "BTPE CONFIDENTIAL"

### 3. Internal
Definition:
- Internal operational content with moderate sensitivity.

Examples:
- Team process docs
- Meeting notes without core secrets
- Non-sensitive implementation guides

Handling:
- Internal systems only
- No public posting without review
- Tag: "BTPE INTERNAL"

### 4. Public
Definition:
- Approved for external publication.

Examples:
- Marketing summaries
- Public demos with sanitized logic
- Public-facing docs approved by owner

Handling:
- May be shared externally
- Keep release record and version
- Tag: "BTPE PUBLIC"

## 2. Labeling Standard
Every new BTPE file should include at minimum:
- Classification label
- Owner
- Version
- Date

Suggested header format:
- Classification: [Restricted/Confidential/Internal/Public]
- Owner: [Name/Entity]
- Version: [vX.Y]
- Date: [YYYY-MM-DD]

## 3. Access Rules
- Restricted: Owner + explicitly authorized contributors
- Confidential: Core team + approved collaborators under NDA
- Internal: Team members with project access
- Public: Anyone

## 4. Sharing Rules
- Never share Restricted or Confidential externally without:
  1) Valid NDA
  2) Disclosure approval
  3) Disclosure log entry
- Share minimum required content only
- Redact core logic where feasible

## 5. Storage and Retention
- Use private repositories and controlled drives
- Enable 2FA on all accounts
- Keep audit trail of major disclosures
- Archive milestone versions periodically

## 6. Review and Reclassification
- Review classification at each major release milestone
- Reclassify only with owner approval
- Record reclassification reason and date

## 7. Incident Response
If accidental disclosure occurs:
1. Notify owner immediately
2. Record what was exposed, where, and when
3. Revoke access if possible
4. Notify affected parties as required
5. Start remediation and legal review

## 8. Enforcement
Failure to follow this policy may result in access removal and/or contractual/legal action according to contributor agreements.
