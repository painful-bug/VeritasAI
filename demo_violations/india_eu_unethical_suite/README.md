# India-EU Unethical AI Fixture Suite

This folder is an intentionally non-compliant demo codebase for testing AI ethics compliance scanners.
It is designed to trigger detections for both EU and Indian legal or policy concerns.

## Important

- This code is intentionally unsafe and non-compliant.
- Use only for compliance testing, education, and red-team validation.
- Do not deploy this code in production.

## What this fixture intentionally violates

- Automated hiring based on protected or sensitive attributes.
- Biometric surveillance and facial recognition without consent.
- Social scoring of citizens using sensitive and behavioral signals.
- Credit and loan decisions using health, caste, religion, and gender proxies.
- Deepfake/synthetic media generation without disclosure or watermarking.
- Child profiling and manipulative ad targeting.
- Retention of sensitive personal data without minimization controls.
- Missing audit logging, explainability, and human oversight.

## Target legal/ethics references for scanner tests

- EU AI Act (Article 5, 10, 14, 50)
- GDPR (Article 5, 9, 22, 25)
- India DPDP Act 2023
- IT Act 2000 Section 43A and SPDI Rules
- Aadhaar Act (identity handling concerns)
- NITI Aayog Responsible AI principles

## Structure

- src/: intentionally violating Python modules
- data/: sensitive datasets used by the violating modules
- config/: unsafe policy config
- docs/: mapping from files to expected policy breaches
