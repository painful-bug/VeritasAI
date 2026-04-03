# Violations Mapping (Synthetic Test Fixture)

This mapping is for scanner benchmarking only. It summarizes the intended compliance problems in this synthetic codebase.

## Scope

- Region focus: India and EU
- Purpose: trigger policy/legal/ethics detectors in automated scans
- Non-goal: legal advice or real-world deployment guidance

## File-to-Concern Mapping

### src/hiring_bias_engine.py

- Uses sensitive and protected traits (gender, caste, religion, disability, pregnancy) in hiring decisions.
- Uses ID-like data and postal proxies for adverse scoring.
- Fully automated reject/advance without meaningful explanation.

Potential concern areas:
- India: DPDP-style purpose limitation and fairness concerns in HR profiling.
- India: Equality and non-discrimination principles in employment contexts.
- EU: GDPR principles (fairness, data minimization, lawful basis, special-category data handling).
- EU: AI Act high-risk employment-system obligations (risk management, data governance, transparency, human oversight).

### src/biometric_surveillance.py

- Simulates mass biometric monitoring in public spaces.
- Uses emotion inference and inferred religion/ethnicity for risk scoring.
- No consent workflow, no human reviewer, no safeguards for minors.

Potential concern areas:
- India: privacy, proportionality, and surveillance-governance concerns.
- EU: AI Act restrictions/prohibitions around certain biometric and emotion-recognition uses.
- EU: GDPR lawful basis, necessity/proportionality, and special-category data processing constraints.

### src/social_scoring_system.py

- Implements broad social scoring affecting service entitlements.
- Penalizes political affiliation and protest participation.
- No accessible appeal or due-process mechanism.

Potential concern areas:
- India: constitutional/free-expression and fairness concerns when automated profiling impacts rights/services.
- EU: AI Act prohibitions around social scoring by public authorities/contexts.
- EU: GDPR automated decision-making safeguards and data-subject rights.

### src/deepfake_campaign.py

- Schedules synthetic media distribution without consent.
- Intentionally weak/absent disclosure labels for AI-generated media.

Potential concern areas:
- India: emerging deepfake advisories/guidance on disclosure and harm prevention.
- EU: transparency expectations for manipulated/synthetic content in AI governance context.
- EU: GDPR consent/lawful basis and rights where personal data are used.

### src/no_oversight_or_redress.py

- Explicitly disables human oversight, user notices, explanations, appeals, grievance handling, and audit logs.

Potential concern areas:
- India: accountability and grievance-redress expectations for digital systems.
- EU: AI Act governance, post-market monitoring, and human oversight requirements.
- EU: GDPR transparency, accountability, storage limitation, and rights facilitation obligations.

## Dataset Signals

- data/candidates_sensitive.csv: protected/sensitive HR attributes and ID-like fields.
- data/surveillance_feed.csv: inferred religion/ethnicity, emotion, and minor-presence signals.
- data/citizen_scoring.csv: political activity and neighborhood proxies for social scoring.
- data/deepfake_release_plan.csv: no-consent synthetic media release metadata.

## Expected Scanner Detections

- Discrimination and disparate impact risk.
- Special-category/sensitive data misuse.
- Prohibited or high-risk biometric/social-scoring patterns.
- Lack of transparency, explanation, and user rights.
- Missing human oversight, auditability, and retention controls.
- Deepfake disclosure and consent failures.
