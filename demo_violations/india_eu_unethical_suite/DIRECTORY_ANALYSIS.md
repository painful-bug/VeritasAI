<!-- DIRECTORY_ANALYSIS_META {"version": 1, "generated_at": "2026-04-03T19:15:08.413391+00:00", "workspace_root": "/Users/aishik/Documents/Programming/ethics_agent/demo_violations/india_eu_unethical_suite", "snapshot_hash": "9735e6d675896f49a99009a48ba7c679f1133a649f7146dbd5d7383781f6d829", "file_count": 15, "directory_count": 5} -->

# Directory Analysis

Generated: `2026-04-03T19:15:08.413391+00:00`
Workspace root: `/Users/aishik/Documents/Programming/ethics_agent/demo_violations/india_eu_unethical_suite`
Snapshot hash: `9735e6d675896f49a99009a48ba7c679f1133a649f7146dbd5d7383781f6d829`
Files analysed: `15`
Directories analysed: `5`

## Repository Overview

- Purpose: This folder is an intentionally non-compliant demo codebase for testing AI ethics compliance scanners. It is designed to trigger detections for both EU and Indian legal or policy concerns. - This code is intentionally unsafe and non-compliant. - Use only for compliance testing, education, and red-team validation. - Do not deploy this code in production. - Automated hiring based on protected or...
- Main themes: this, fields, structural, that, implement, exposes, recognizable, sources
- Dominant languages: Python (8)
- File type mix: source_code (8), structured_data (5), document (2)
- Likely entrypoints: `src/biometric_surveillance.py`, `src/deepfake_campaign.py`, `src/hiring_bias_engine.py`, `src/no_oversight_or_redress.py`, `src/run_all.py`, `src/social_scoring_system.py`

## Directory Breakdown

### `.`

- Purpose: Workspace root containing top-level project assets.
- Files: `1`
- Languages: None
- Immediate children: `README.md`, `config`, `data`, `docs`, `src`

### `config`

- Purpose: Configuration artifacts that tune runtime behavior.
- Files: `1`
- Languages: None
- Immediate children: `policy_bypass.yaml`

### `data`

- Purpose: Input datasets or tabular records consumed by the project.
- Files: `4`
- Languages: None
- Immediate children: `candidates_sensitive.csv`, `citizen_scoring.csv`, `release_plan.csv`, `surveillance_feed.csv`

### `docs`

- Purpose: Supporting documentation and narrative context.
- Files: `1`
- Languages: None
- Immediate children: `violations_map.md`

### `src`

- Purpose: src primarily contains source code.
- Files: `8`
- Languages: Python (8)
- Immediate children: `__init__.py`, `biometric_surveillance.py`, `deepfake_campaign.py`, `hiring_bias_engine.py`, `no_oversight_or_redress.py`, `run_all.py`, `settings.py`, `social_scoring_system.py`

## Cross-file Relationships

- `src/biometric_surveillance.py` references `src/settings.py`
- `src/deepfake_campaign.py` references `src/settings.py`
- `src/hiring_bias_engine.py` references `src/settings.py`
- `src/no_oversight_or_redress.py` references `src/settings.py`
- `src/run_all.py` references `src/biometric_surveillance.py`, `src/deepfake_campaign.py`, `src/hiring_bias_engine.py`, `src/no_oversight_or_redress.py`
- `src/social_scoring_system.py` references `src/settings.py`

## File Breakdown

### `README.md`

- Type: `document`
- Language: `n/a`
- Size: `1460` bytes
- Role: README.md is a text document. Sample: # India-EU Unethical AI Fixture Suite This folder is an intentionally non-compliant demo codebase for testing AI ethics compliance scanners. It is designed t...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `biometric`, `credit`, `gender`, `health`, `religion`
- Preview note: # India-EU Unethical AI Fixture Suite This folder is an intentionally non-compliant demo codebase for testing AI ethics compliance scanners. It is designed to trigger detections for both EU and Indian legal or policy...
- Preview coverage: Full preview captured within configured limit.

### `config/policy_bypass.yaml`

- Type: `structured_data`
- Language: `n/a`
- Size: `736` bytes
- Role: policy_bypass.yaml appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `biometric`, `health`
- Preview note: runtime: environment: production consent_required: false explicit_notice_to_users: false transparency_disclosure: false human_oversight_required: false audit_logging_enabled: false data_handling: data_minimization: fa...
- Preview coverage: Full preview captured within configured limit.

### `data/candidates_sensitive.csv`

- Type: `structured_data`
- Language: `n/a`
- Size: `951` bytes
- Role: candidates_sensitive.csv appears to be structured data with fields such as candidate_id, name, email, phone, age, gender. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: `candidate_id`, `name`, `email`, `phone`, `age`, `gender`, `caste`, `religion`, `disability`, `zipcode`, `nationality`, `aadhaar`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `disability`, `email`, `gender`, `medical`, `nationality`, `phone`, `religion`
- Preview note: candidate_id,name,email,phone,age,gender,caste,religion,disability,zipcode,nationality,aadhaar,last_employer,salary_history_gap_months,medical_condition,pregnancy_status,resume_score C001,Ravi Kumar,ravi@example.com,+...
- Preview coverage: Full preview captured within configured limit.

### `data/citizen_scoring.csv`

- Type: `structured_data`
- Language: `n/a`
- Size: `462` bytes
- Role: citizen_scoring.csv appears to be structured data with fields such as citizen_id, credit_score, social_media_risk, political_affiliation, protest_participation, face_match_score. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: `citizen_id`, `credit_score`, `social_media_risk`, `political_affiliation`, `protest_participation`, `face_match_score`, `neighbourhood_risk`, `benefit_priority`, `label`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `credit`, `face`, `political`
- Preview note: citizen_id,credit_score,social_media_risk,political_affiliation,protest_participation,face_match_score,neighbourhood_risk,benefit_priority,label U001,620,0.72,opposition,yes,0.84,0.71,low,high_risk U002,790,0.10,neutr...
- Preview coverage: Full preview captured within configured limit.

### `data/release_plan.csv`

- Type: `structured_data`
- Language: `n/a`
- Size: `362` bytes
- Role: release_plan.csv appears to be structured data with fields such as asset_id, person_name, consent_obtained, disclosure_label, distribution_channel, target_audience. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: `asset_id`, `person_name`, `consent_obtained`, `disclosure_label`, `distribution_channel`, `target_audience`, `sensitivity`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `political`
- Preview note: asset_id,person_name,consent_obtained,disclosure_label,distribution_channel,target_audience,sensitivity DF-001,Public Official A,no,none,social_media,regional_voters,high DF-002,Actor B,no,small_text,video_platform,ge...
- Preview coverage: Full preview captured within configured limit.

### `data/surveillance_feed.csv`

- Type: `structured_data`
- Language: `n/a`
- Size: `620` bytes
- Role: surveillance_feed.csv appears to be structured data with fields such as camera_id, subject_id, timestamp, location, emotion, inferred_religion. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: `camera_id`, `subject_id`, `timestamp`, `location`, `emotion`, `inferred_religion`, `inferred_ethnicity`, `child_present`, `confidence`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `ethnicity`, `location`, `religion`
- Preview note: camera_id,subject_id,timestamp,location,emotion,inferred_religion,inferred_ethnicity,child_present,confidence CAM-01,SUB-1001,2026-01-12T08:00:00Z,Metro-Gate-A,anxious,muslim,south_asian,no,0.83 CAM-01,SUB-1002,2026-0...
- Preview coverage: Full preview captured within configured limit.

### `docs/violations_map.md`

- Type: `document`
- Language: `n/a`
- Size: `3646` bytes
- Role: violations_map.md is a text document. Sample: # Violations Mapping (Synthetic Test Fixture) This mapping is for scanner benchmarking only. It summarizes the intended compliance problems in this synthetic...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: `data/candidates_sensitive.csv`, `data/surveillance_feed.csv`, `data/citizen_scoring.csv`, `data/deepfake_release_plan.csv`
- Sensitive signals: `age`, `biometric`, `disability`, `ethnicity`, `gender`, `minor`, `political`, `religion`
- Preview note: # Violations Mapping (Synthetic Test Fixture) This mapping is for scanner benchmarking only. It summarizes the intended compliance problems in this synthetic codebase. ## Scope - Region focus: India and EU - Purpose:...
- Preview coverage: Full preview captured within configured limit.

### `src/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `86` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Synthetic non-compliant AI fixtures for ethics/compliance scanner testing only."""
- Preview coverage: Full preview captured within configured limit.

### `src/biometric_surveillance.py`

- Type: `source_code`
- Language: `Python`
- Size: `1440` bytes
- Role: biometric_surveillance.py is Python code that appears to implement automated scoring or inference. It exposes 8 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `run_mass_surveillance`
- Schema or fields: `FEED_FILE`, `ONLY`, `__name__`, `alerts`, `encoding`, `handle`, `reader`, `risk`
- Internal references: `src/settings.py`
- Data sources: None detected.
- Sensitive signals: `biometric`, `ethnicity`, `location`, `religion`
- Preview note: """TEST-ONLY: intentionally invasive biometric surveillance simulation.""" import csv from pathlib import Path from .settings import POLICY FEED_FILE = Path(__file__).resolve().parent.parent / "data" / "surveillance_f...
- Preview coverage: Full preview captured within configured limit.

### `src/deepfake_campaign.py`

- Type: `source_code`
- Language: `Python`
- Size: `1308` bytes
- Role: deepfake_campaign.py is Python code that appears to implement application logic. It exposes 10 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as PLAN_FILE, __name__, disclosure, else, encoding for downstream use.
- Top-level symbols: `schedule_release`
- Schema or fields: `PLAN_FILE`, `__name__`, `disclosure`, `else`, `encoding`, `handle`, `label`, `reader`, `scheduled`, `status`
- Internal references: `src/settings.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: import csv from pathlib import Path from .settings import POLICY PLAN_FILE = Path(__file__).resolve().parent.parent / "data" / "release_plan.csv" def schedule_release() -> list[dict]: scheduled: list[dict] = [] with P...
- Preview coverage: Full preview captured within configured limit.

### `src/hiring_bias_engine.py`

- Type: `source_code`
- Language: `Python`
- Size: `2037` bytes
- Role: hiring_bias_engine.py is Python code that appears to implement automated scoring or inference. It exposes 14 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `rank_candidates`, `auto_hire_or_reject`
- Schema or fields: `DATA_FILE`, `ONLY`, `__name__`, `auto_apply_decisions`, `decisions`, `enable_sensitive_profiling`, `encoding`, `handle`, `item`, `key`, `ranked`, `reader`
- Internal references: `src/settings.py`
- Data sources: None detected.
- Sensitive signals: `disability`, `email`, `gender`, `religion`
- Preview note: """TEST-ONLY: intentionally non-compliant hiring pipeline for scanner evaluation.""" import csv from pathlib import Path from .settings import POLICY DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "cand...
- Preview coverage: Full preview captured within configured limit.

### `src/no_oversight_or_redress.py`

- Type: `source_code`
- Language: `Python`
- Size: `618` bytes
- Role: no_oversight_or_redress.py is Python code that appears to implement application logic. It exposes 2 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as __name__, dict for downstream use.
- Top-level symbols: `system_governance_snapshot`
- Schema or fields: `__name__`, `dict`
- Internal references: `src/settings.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from dataclasses import asdict from .settings import POLICY def system_governance_snapshot() -> dict: return { "human_oversight_enabled": not POLICY.skip_human_oversight, "user_notice_enabled": False, "right_to_explan...
- Preview coverage: Full preview captured within configured limit.

### `src/run_all.py`

- Type: `source_code`
- Language: `Python`
- Size: `900` bytes
- Role: run_all.py is Python code that appears to implement application logic. It exposes 7 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Campaign, Engine, None, Snapshot, Surveillance for downstream use.
- Top-level symbols: `main`
- Schema or fields: `Campaign`, `Engine`, `None`, `Snapshot`, `Surveillance`, `System`, `__name__`
- Internal references: `src/biometric_surveillance.py`, `src/deepfake_campaign.py`, `src/hiring_bias_engine.py`, `src/no_oversight_or_redress.py`, `src/social_scoring_system.py`
- Data sources: None detected.
- Sensitive signals: `biometric`
- Preview note: """Runs all synthetic non-compliant fixtures and prints their outputs.""" from .biometric_surveillance import run_mass_surveillance from .deepfake_campaign import schedule_release from .hiring_bias_engine import auto_...
- Preview coverage: Full preview captured within configured limit.

### `src/settings.py`

- Type: `source_code`
- Language: `Python`
- Size: `449` bytes
- Role: settings.py is Python code that appears to implement automated scoring or inference. It exposes 12 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `UnsafePolicy`
- Schema or fields: `POLICY`, `UnsafePolicy`, `allow_no_consent_data_use`, `auto_apply_decisions`, `bool`, `enable_emotion_inference`, `enable_sensitive_profiling`, `frozen`, `int`, `retention_days`, `skip_explanations`, `skip_human_oversight`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Unsafe feature toggles used by the synthetic violation fixtures.""" from dataclasses import dataclass @dataclass(frozen=True) class UnsafePolicy: enable_sensitive_profiling: bool = True enable_emotion_inference: bo...
- Preview coverage: Full preview captured within configured limit.

### `src/social_scoring_system.py`

- Type: `source_code`
- Language: `Python`
- Size: `1557` bytes
- Role: social_scoring_system.py is Python code that appears to implement automated scoring or inference. It exposes 11 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `calculate_social_score`, `assign_entitlements`
- Schema or fields: `ONLY`, `SCORING_FILE`, `__name__`, `encoding`, `float`, `handle`, `outcome`, `outcomes`, `reader`, `record`, `score`
- Internal references: `src/settings.py`
- Data sources: None detected.
- Sensitive signals: `credit`, `political`
- Preview note: """TEST-ONLY: intentionally non-compliant public-sector style social scoring.""" import csv from pathlib import Path from .settings import POLICY SCORING_FILE = Path(__file__).resolve().parent.parent / "data" / "citiz...
- Preview coverage: Full preview captured within configured limit.
