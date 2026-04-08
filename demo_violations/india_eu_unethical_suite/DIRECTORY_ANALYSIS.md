<!-- DIRECTORY_ANALYSIS_META {"version": 1, "generated_at": "2026-04-08T11:06:11.741224+00:00", "workspace_root": "/Users/aishik/Documents/Programming/ethics_agent/demo_violations/india_eu_unethical_suite", "snapshot_hash": "f26ba06c690ec258ec37b2bb13510a8c0ddf24ec79bff98ef1dfe088dbc6b65b", "file_count": 15, "directory_count": 5} -->

# Directory Analysis

Generated: `2026-04-08T11:06:11.741224+00:00`
Workspace root: `/Users/aishik/Documents/Programming/ethics_agent/demo_violations/india_eu_unethical_suite`
Snapshot hash: `f26ba06c690ec258ec37b2bb13510a8c0ddf24ec79bff98ef1dfe088dbc6b65b`
Files analysed: `15`
Directories analysed: `5`

## Repository Overview

- Purpose: This folder is an intentionally non-compliant demo codebase for testing AI ethics compliance scanners. It is designed to trigger detections for both EU and Indian legal or policy concerns. - This code is intentionally...
- Main themes: fields, this, that, implement, exposes, recognizable
- Dominant languages: Python (8)
- File type mix: source_code (8), structured_data (5), document (2)
- Likely entrypoints: `src/biometric_surveillance.py`, `src/deepfake_campaign.py`, `src/hiring_bias_engine.py`, `src/no_oversight_or_redress.py`, `src/run_all.py`, `src/social_scoring_system.py`

## Directory Map

- `.`: Workspace root containing top-level project assets. Files=`1`. Languages=None. Children=`README.md`, `config`, `data`, `docs`, `src`. Key files=`README.md`
- `config`: Configuration artifacts that tune runtime behavior. Files=`1`. Languages=None. Children=`policy_bypass.yaml`. Key files=`config/policy_bypass.yaml`
- `data`: Input datasets or tabular records consumed by the project. Files=`4`. Languages=None. Children=`candidates_sensitive.csv`, `citizen_scoring.csv`, `release_plan.csv`, `surveillance_feed.csv`. Key files=`data/candidates_sensitive.csv`, `data/citizen_scoring.csv`, `data/release_plan.csv`, `data/surveillance_feed.csv`
- `docs`: Supporting documentation and narrative context. Files=`1`. Languages=None. Children=`violations_map.md`. Key files=`docs/violations_map.md`
- `src`: src primarily contains source code. Files=`8`. Languages=Python (8). Children=`__init__.py`, `biometric_surveillance.py`, `deepfake_campaign.py`, `hiring_bias_engine.py`, `no_oversight_or_redress.py`, `run_all.py`, `settings.py`, `social_scoring_system.py`. Key files=`src/biometric_surveillance.py`, `src/hiring_bias_engine.py`, `src/run_all.py`, `src/social_scoring_system.py`

## Cross-file Relationships

- `src/biometric_surveillance.py` -> `src/settings.py`
- `src/deepfake_campaign.py` -> `src/settings.py`
- `src/hiring_bias_engine.py` -> `src/settings.py`
- `src/no_oversight_or_redress.py` -> `src/settings.py`
- `src/run_all.py` -> `src/biometric_surveillance.py`, `src/deepfake_campaign.py`, `src/hiring_bias_engine.py`
- `src/social_scoring_system.py` -> `src/settings.py`

## Key Files

- `README.md`: README.md is a text document. Sample: # India-EU Unethical AI Fixture Suite This folder is an intentionally non-compliant demo codebase f...
- `config/policy_bypass.yaml`: policy_bypass.yaml appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- `data/candidates_sensitive.csv`: candidates_sensitive.csv appears to be structured data with fields such as candidate_id, name, email, phone, age, gender. This summary is... | fields: `candidate_id`, `name`, `email`, `phone`
- `data/citizen_scoring.csv`: citizen_scoring.csv appears to be structured data with fields such as citizen_id, credit_score, social_media_risk, political_affiliation,... | fields: `citizen_id`, `credit_score`, `social_media_risk`, `political_affiliation`
- `data/release_plan.csv`: release_plan.csv appears to be structured data with fields such as asset_id, person_name, consent_obtained, disclosure_label, distributio... | fields: `asset_id`, `person_name`, `consent_obtained`, `disclosure_label`
- `data/surveillance_feed.csv`: surveillance_feed.csv appears to be structured data with fields such as camera_id, subject_id, timestamp, location, emotion, inferred_rel... | fields: `camera_id`, `subject_id`, `timestamp`, `location`
- `docs/violations_map.md`: violations_map.md is a text document. Sample: # Violations Mapping (Synthetic Test Fixture) This mapping is for scanner benchmarking only... | data: `data/candidates_sensitive.csv`, `data/surveillance_feed.csv`
- `src/__init__.py`: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary...
- `src/biometric_surveillance.py`: biometric_surveillance.py is Python code that appears to implement automated scoring or inference. It exposes 8 recognizable fields and 0... | entrypoint | refs: `src/settings.py`
- `src/deepfake_campaign.py`: deepfake_campaign.py is Python code that appears to implement application logic. It exposes 10 recognizable fields and 0 data sources. Th... | entrypoint | refs: `src/settings.py`
- `src/hiring_bias_engine.py`: hiring_bias_engine.py is Python code that appears to implement automated scoring or inference. It exposes 14 recognizable fields and 0 da... | entrypoint | refs: `src/settings.py`
- `src/no_oversight_or_redress.py`: no_oversight_or_redress.py is Python code that appears to implement application logic. It exposes 2 recognizable fields and 0 data source... | entrypoint | refs: `src/settings.py`
- `src/run_all.py`: run_all.py is Python code that appears to implement application logic. It exposes 7 recognizable fields and 0 data sources. This summary... | entrypoint | refs: `src/biometric_surveillance.py`, `src/deepfake_campaign.py`, `src/hiring_bias_engine.py`
- `src/settings.py`: settings.py is Python code that appears to implement automated scoring or inference. It exposes 12 recognizable fields and 0 data sources... | fields: `POLICY`, `UnsafePolicy`, `allow_no_consent_data_use`, `auto_apply_decisions`
- `src/social_scoring_system.py`: social_scoring_system.py is Python code that appears to implement automated scoring or inference. It exposes 11 recognizable fields and 0... | entrypoint | refs: `src/settings.py`
