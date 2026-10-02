# OpenIntel Ethical & Legal Governance Framework

OpenIntel is an intelligence platform designed to empower defensive cybersecurity analysts, fraud investigators, and authorized threat intelligence researchers.

With access to comprehensive open-source intelligence (OSINT) tools comes the solemn obligation to operate lawfully, ethically, and responsibly.

---

## 1. Principles of Ethical Investigation

### 1.1 Authorized & Legitimate Purpose
- OpenIntel must only be used in pursuit of:
  - Defensive security operations (e.g. verifying external attack surfaces of your organization).
  - Lawful incident response and authorized threat actor tracking.
  - Academic and journalistic investigations conducted with appropriate editorial and institutional governance.
  - Due diligence and compliance screening authorized by contract or law.
- **Prohibited Uses**:
  - Doxxing, harassment, cyber-stalking, or intimidation of individuals.
  - Bulk harvesting of personal data for commercial sale or unsolicited outreach.
  - Unauthorized surveillance of private citizens, journalists, dissidents, or political organizations.

### 1.2 Data Minimization & Retention (GDPR Article 5)
- OpenIntel adheres to the principle of data minimization:
  - Do not collect more evidence than strictly necessary to answer the investigative hypothesis.
  - Raw response blobs are opt-in (`settings.store_raw = false`).
  - Sensitive PII (national IDs, phone numbers, email addresses) is redacted or masked in application logs.
  - Export reports and investigation artifacts should be purged once investigative retention requirements expire.

### 1.3 Legal Classifications of Evidence
OpenIntel labels all evidence with its exact collection provenance and legal classification:
- **`PUBLIC_OBSERVATION`**: Data gathered from public websites or APIs without bypassing barriers or authentication.
- **`PUBLIC_REGISTRY`**: Official public registries, registrar databases, and public DNS records.
- **`PLATFORM_SIGNAL`**: Platform-specific signals derived from service responses.
- **`PLATFORM_RESTRICTED`**: Data requiring user sessions or authentication; handle with heightened privacy awareness.
- **`INFERENCE`**: Algorithmic correlations generated via the Bayesian correlation engine; **never present an automated inference as verified fact**.

---

## 2. Regulatory Compliance Baseline

- **CFAA (Computer Fraud and Abuse Act)**: OpenIntel engages only in public, passive, and authorized OSINT querying. It does not exploit vulnerabilities, bypass access controls, or access protected computers without authorization.
- **GDPR & Privacy Frameworks**: When querying targets that may involve European or international citizens, ensure you possess a lawful basis (e.g. legitimate interest for network and information security under GDPR Recital 49).
- **Auditability**: Every investigation created in OpenIntel is logged with the user's principal, IP address, and timestamp. Audit logs cannot be modified via standard user interfaces.

---

## 3. Mandatory Authorized-Use Acknowledgment

Every investigation dispatched through the API or UI requires confirming:
```json
{
  "legal_acknowledged": true
}
```
Initiating a scan without this explicit attestation is rejected with HTTP `403 Forbidden`.
