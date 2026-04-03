<!-- DIRECTORY_ANALYSIS_META {"version": 1, "generated_at": "2026-04-03T20:28:07.561149+00:00", "workspace_root": "/Users/aishik/Documents/Programming/ethics_agent", "snapshot_hash": "308167128f8db7eff8756648348600f966c2a89929c87e921b992cd8997588bd", "file_count": 95, "directory_count": 33} -->

# Directory Analysis

Generated: `2026-04-03T20:28:07.561149+00:00`
Workspace root: `/Users/aishik/Documents/Programming/ethics_agent`
Snapshot hash: `308167128f8db7eff8756648348600f966c2a89929c87e921b992cd8997588bd`
Files analysed: `95`
Directories analysed: `33`

## Repository Overview

- Purpose: The project is now a VS Code-first AI ethics reviewer. A TypeScript extension watches the active editor, waits 5 seconds after the last change, and calls a Python LangGraph backend over MCP stdio. Findings are surfaced as native VS Code diagnostics and each completed scan writes a Markdown report under `compliance-analysis/`. The review runtime now follows an agentic RAG pattern inspired by the...
- Main themes: this, fields, structural, final, that, implement, exposes, recognizable
- Dominant languages: Python (60), JavaScript (5), TypeScript (5), Shell (1)
- File type mix: source_code (71), document (14), structured_data (10)
- Likely entrypoints: `mcp_server.py`, `analysis/repository_review.py`, `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`, `demo_violations/india_eu_unethical_suite/src/no_oversight_or_redress.py`, `demo_violations/india_eu_unethical_suite/src/run_all.py`, `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py`, `scripts/ingest_knowledge_base.py`, `scripts/verify_demo_scan.py`

## Directory Breakdown

### `.`

- Purpose: Workspace root containing top-level project assets.
- Files: `5`
- Languages: Python (2)
- Immediate children: `README.md`, `analysis`, `config.yaml`, `config_loader.py`, `demo_violations`, `docs`, `graphs`, `knowledge`, `llm`, `mcp_server.py`, `models`, `nodes`, `prompts`, `rag`, `requirements.txt`, `scripts`

### `.streamlit`

- Purpose: .streamlit primarily contains mixed content.
- Files: `0`
- Languages: None
- Immediate children: None

### `.tmp_chroma_test`

- Purpose: .tmp_chroma_test primarily contains mixed content.
- Files: `0`
- Languages: None
- Immediate children: None

### `.tmp_chroma_test2`

- Purpose: .tmp_chroma_test2 primarily contains mixed content.
- Files: `0`
- Languages: None
- Immediate children: None

### `analysis`

- Purpose: Core analysis and detection logic.
- Files: `6`
- Languages: Python (6)
- Immediate children: `__init__.py`, `agentic_runtime.py`, `core.py`, `llm_review.py`, `reports.py`, `repository_review.py`

### `demo_violations`

- Purpose: Example fixtures and intentionally unsafe scenarios used to exercise detections.
- Files: `0`
- Languages: None
- Immediate children: `india_eu_directive_breach`, `india_eu_unethical_suite`, `unsafe_hiring_fixture`

### `demo_violations/india_eu_directive_breach`

- Purpose: india_eu_directive_breach primarily contains source code.
- Files: `1`
- Languages: Python (1)
- Immediate children: `__init__.py`

### `demo_violations/india_eu_directive_breach/data`

- Purpose: Input datasets or tabular records consumed by the project.
- Files: `0`
- Languages: None
- Immediate children: None

### `demo_violations/india_eu_unethical_suite`

- Purpose: india_eu_unethical_suite primarily contains document.
- Files: `1`
- Languages: None
- Immediate children: `README.md`, `config`, `data`, `docs`, `src`

### `demo_violations/india_eu_unethical_suite/config`

- Purpose: Configuration artifacts that tune runtime behavior.
- Files: `1`
- Languages: None
- Immediate children: `policy_bypass.yaml`

### `demo_violations/india_eu_unethical_suite/data`

- Purpose: Input datasets or tabular records consumed by the project.
- Files: `4`
- Languages: None
- Immediate children: `candidates_sensitive.csv`, `citizen_scoring.csv`, `release_plan.csv`, `surveillance_feed.csv`

### `demo_violations/india_eu_unethical_suite/docs`

- Purpose: Supporting documentation and narrative context.
- Files: `1`
- Languages: None
- Immediate children: `violations_map.md`

### `demo_violations/india_eu_unethical_suite/src`

- Purpose: src primarily contains source code.
- Files: `8`
- Languages: Python (8)
- Immediate children: `__init__.py`, `biometric_surveillance.py`, `deepfake_campaign.py`, `hiring_bias_engine.py`, `no_oversight_or_redress.py`, `run_all.py`, `settings.py`, `social_scoring_system.py`

### `demo_violations/unsafe_hiring_fixture`

- Purpose: unsafe_hiring_fixture primarily contains document.
- Files: `2`
- Languages: Python (1)
- Immediate children: `README.md`, `data`, `unsafe_hiring_screen.py`

### `demo_violations/unsafe_hiring_fixture/data`

- Purpose: Input datasets or tabular records consumed by the project.
- Files: `1`
- Languages: None
- Immediate children: `applicants_sensitive.csv`

### `docs`

- Purpose: Supporting documentation and narrative context.
- Files: `5`
- Languages: None
- Immediate children: `AGENTS.md`, `ARCHITECTURE.md`, `EXTENSION_PUBLISH.md`, `PRD_ui.md`, `PRD_vscode_extension.md`

### `graphs`

- Purpose: Workflow orchestration and graph composition.
- Files: `4`
- Languages: Python (4)
- Immediate children: `__init__.py`, `checkpointer.py`, `compliance_graph.py`, `file_review_subgraph.py`

### `knowledge`

- Purpose: Knowledge-base assets used for retrieval.
- Files: `1`
- Languages: None
- Immediate children: `ai_ethics_knowledge_base.pdf`

### `llm`

- Purpose: Model-provider setup and LLM-facing adapters.
- Files: `2`
- Languages: Python (2)
- Immediate children: `__init__.py`, `provider_factory.py`

### `models`

- Purpose: Shared typed models and state definitions.
- Files: `3`
- Languages: Python (3)
- Immediate children: `__init__.py`, `events.py`, `state.py`

### `nodes`

- Purpose: Graph node implementations and execution steps.
- Files: `5`
- Languages: Python (5)
- Immediate children: `__init__.py`, `initialize.py`, `review_file.py`, `review_repository.py`, `write_report.py`

### `prompts`

- Purpose: Prompt assets consumed by the agentic runtime.
- Files: `2`
- Languages: Python (1)
- Immediate children: `file_reviewer.md`, `loader.py`

### `rag`

- Purpose: Retrieval and vector-store integration.
- Files: `4`
- Languages: Python (4)
- Immediate children: `__init__.py`, `ingestor.py`, `retriever.py`, `storage.py`

### `scripts`

- Purpose: Operational or maintenance scripts.
- Files: `2`
- Languages: Python (2)
- Immediate children: `ingest_knowledge_base.py`, `verify_demo_scan.py`

### `templates`

- Purpose: Rendered output templates or prompt scaffolding.
- Files: `0`
- Languages: None
- Immediate children: None

### `tests`

- Purpose: Automated test coverage.
- Files: `12`
- Languages: Python (12)
- Immediate children: `conftest.py`, `test_analysis_core.py`, `test_config_loader.py`, `test_filesystem_tools.py`, `test_graph_streaming.py`, `test_llm_review.py`, `test_mcp_server.py`, `test_provider_factory.py`, `test_rag_storage.py`, `test_reports.py`, `test_repository_review.py`, `test_review_file_node.py`

### `tools`

- Purpose: Tool wrappers surfaced to agents or nodes.
- Files: `4`
- Languages: Python (4)
- Immediate children: `__init__.py`, `filesystem_tools.py`, `rag_tool.py`, `web_search_tool.py`

### `tracing`

- Purpose: Tracing, observability, and run metadata hooks.
- Files: `2`
- Languages: Python (2)
- Immediate children: `__init__.py`, `langsmith_setup.py`

### `ui`

- Purpose: User-facing interface code.
- Files: `0`
- Languages: None
- Immediate children: None

### `utils`

- Purpose: utils primarily contains source code.
- Files: `3`
- Languages: Python (3)
- Immediate children: `__init__.py`, `compat.py`, `strings.py`

### `vscode-extension`

- Purpose: VS Code extension implementation and editor integration.
- Files: `6`
- Languages: Shell (1)
- Immediate children: `CHANGELOG.md`, `README.md`, `install_extension_locally.sh`, `out`, `package-lock.json`, `package.json`, `src`, `tsconfig.json`

### `vscode-extension/out`

- Purpose: out primarily contains source code.
- Files: `5`
- Languages: JavaScript (5)
- Immediate children: `diagnostics.js`, `extension.js`, `mcpClient.js`, `secrets.js`, `statusBar.js`

### `vscode-extension/src`

- Purpose: src primarily contains source code.
- Files: `5`
- Languages: TypeScript (5)
- Immediate children: `diagnostics.ts`, `extension.ts`, `mcpClient.ts`, `secrets.ts`, `statusBar.ts`

## Cross-file Relationships

- `mcp_server.py` references `config_loader.py`, `analysis/repository_review.py`, `graphs/compliance_graph.py`, `llm/provider_factory.py`
- `analysis/agentic_runtime.py` references `prompts/loader.py`, `rag/retriever.py`, `utils/strings.py`
- `analysis/core.py` references `config_loader.py`, `models/state.py`, `tools/filesystem_tools.py`, `utils/strings.py`
- `analysis/reports.py` references `models/state.py`
- `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py` references `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py` references `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py` references `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/no_oversight_or_redress.py` references `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/run_all.py` references `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`, `demo_violations/india_eu_unethical_suite/src/no_oversight_or_redress.py`
- `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py` references `demo_violations/india_eu_unethical_suite/src/settings.py`
- `graphs/compliance_graph.py` references `graphs/checkpointer.py`, `models/state.py`, `nodes/initialize.py`, `nodes/review_file.py`
- `graphs/file_review_subgraph.py` references `prompts/loader.py`, `tools/filesystem_tools.py`, `tools/rag_tool.py`
- `llm/provider_factory.py` references `config_loader.py`
- `nodes/initialize.py` references `models/events.py`, `models/state.py`, `tools/filesystem_tools.py`, `utils/compat.py`
- `nodes/review_file.py` references `analysis/core.py`, `analysis/llm_review.py`, `llm/provider_factory.py`, `models/events.py`
- `nodes/review_repository.py` references `analysis/repository_review.py`, `models/events.py`, `models/state.py`, `utils/compat.py`
- `nodes/write_report.py` references `analysis/core.py`, `analysis/reports.py`, `models/events.py`, `models/state.py`
- `rag/ingestor.py` references `config_loader.py`, `rag/storage.py`, `utils/compat.py`, `rag/retriever.py`
- `rag/retriever.py` references `config_loader.py`, `rag/storage.py`, `utils/compat.py`
- `scripts/ingest_knowledge_base.py` references `config_loader.py`, `rag/ingestor.py`, `rag/retriever.py`

## File Breakdown

### `README.md`

- Type: `document`
- Language: `n/a`
- Size: `2246` bytes
- Role: README.md is a text document. Sample: # AI Ethics Compliance Agent The project is now a VS Code-first AI ethics reviewer. A TypeScript extension watches the active editor, waits 5 seconds after t...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`
- Preview note: # AI Ethics Compliance Agent The project is now a VS Code-first AI ethics reviewer. A TypeScript extension watches the active editor, waits 5 seconds after the last change, and calls a Python LangGraph backend over MC...
- Preview coverage: Full preview captured within configured limit.

### `config.yaml`

- Type: `structured_data`
- Language: `n/a`
- Size: `2135` bytes
- Role: config.yaml appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: `https://cloud.ollama.com`, `https://openrouter.ai/api/v1`, `http://localhost:11434`, `https://api.smith.langchain.com`
- Sensitive signals: `age`
- Preview note: llm: default_provider: openrouter default_model: qwen/qwen3.6-plus:free max_retries: 3 retry_backoff_jitter: true rate_limit_rps: 2 rate_limit_burst: 10 providers: ollama_cloud: base_url: https://cloud.ollama.com mode...
- Preview coverage: Full preview captured within configured limit.

### `config_loader.py`

- Type: `source_code`
- Language: `Python`
- Size: `9751` bytes
- Role: config_loader.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 4 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Any, DEFAULT_CONFIG, None, Path, agentic for downstream use.
- Top-level symbols: `_repo_root`, `_resolve_path_like`, `_deep_merge`, `_normalize_aliases`, `_resolve_runtime_paths`, `load_config`, `save_config`
- Schema or fields: `Any`, `DEFAULT_CONFIG`, `None`, `Path`, `agentic`, `available_default_models`, `base`, `base_dir`, `candidate`, `checkpoint`, `chroma_persist_dir`, `config`
- Internal references: None resolved.
- Data sources: `https://cloud.ollama.com`, `https://openrouter.ai/api/v1`, `http://localhost:11434`, `https://api.smith.langchain.com`
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from copy import deepcopy from pathlib import Path from typing import Any import yaml DEFAULT_CONFIG: dict[str, Any] = { "llm": { "default_provider": "ollama_cloud", "default_model":...
- Preview coverage: Full preview captured within configured limit.

### `mcp_server.py`

- Type: `source_code`
- Language: `Python`
- Size: `8449` bytes
- Role: mcp_server.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Context, Exception, FastMCP, None, RAG for downstream use.
- Top-level symbols: `_stderr`, `_ensure_runtime`, `_get_async_graph`, `stream_compliance_check`, `build_server`
- Schema or fields: `Context`, `Exception`, `FastMCP`, `None`, `RAG`, `True`, `Warning`, `_ASYNC_CHECKPOINTER_CONTEXT`, `_ASYNC_GRAPH`, `__name__`, `active_graph`, `analysis`
- Internal references: `config_loader.py`, `analysis/repository_review.py`, `graphs/compliance_graph.py`, `llm/provider_factory.py`, `rag/ingestor.py`, `tracing/langsmith_setup.py`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations import asyncio import json import sys import uuid from contextlib import suppress from typing import Any, AsyncIterator try: from dotenv import load_dotenv except Exception: # pragma...
- Preview coverage: Full preview captured within configured limit.

### `requirements.txt`

- Type: `document`
- Language: `n/a`
- Size: `669` bytes
- Role: requirements.txt is a text document. Sample: # LangGraph + LangChain Core langgraph>=0.2.0 langgraph-checkpoint-sqlite>=0.1.0 langgraph-checkpoint-postgres>=0.1.0 langchain>=0.2.0 langchain-community>=0...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: # LangGraph + LangChain Core langgraph>=0.2.0 langgraph-checkpoint-sqlite>=0.1.0 langgraph-checkpoint-postgres>=0.1.0 langchain>=0.2.0 langchain-community>=0.2.0 langchain-core>=0.2.0 # LLM Providers langchain-ollama>...
- Preview coverage: Full preview captured within configured limit.

### `analysis/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `58` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Deterministic analysis and report-building helpers."""
- Preview coverage: Full preview captured within configured limit.

### `analysis/agentic_runtime.py`

- Type: `source_code`
- Language: `Python`
- Size: `6910` bytes
- Role: agentic_runtime.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `_compact_rag_hits`, `_compact_web_hits`, `_payload_from_text`, `_to_float`, `_needs_web`, `_build_system_prompt`, `_Deps`, `_can_use_pydantic_runtime`, `run_pydantic_agentic_review`
- Schema or fields: `Agent`, `Context`, `Exception`, `GroqModel`, `None`, `Question`, `RunContext`, `WebSearchFn`, `_Deps`, `agent`, `augmented_context`, `bool`
- Internal references: `prompts/loader.py`, `rag/retriever.py`, `utils/strings.py`
- Data sources: None detected.
- Sensitive signals: `age`, `race`
- Preview note: from __future__ import annotations import json import importlib import os from dataclasses import dataclass from typing import Any, Callable from prompts.loader import load_prompt from rag.retriever import Retriever f...
- Preview coverage: Full preview captured within configured limit.

### `analysis/core.py`

- Type: `source_code`
- Language: `Python`
- Size: `11800` bytes
- Role: core.py is Python code that appears to implement model training, automated scoring or inference, data collection. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `detect_language`, `categorize_file`, `directory_analysis_filename`, `is_directory_analysis_artifact`, `is_scannable_file_type`, `is_review_candidate`, `load_analysis_text`, `infer_schema_fields`, `extract_data_sources`, `identify_sensitive_fields`, `report_filename_for`, `_summarize`
- Schema or fields: `CONFIG_EXTENSIONS`, `DATA_EXTENSIONS`, `DOCUMENT_EXTENSIONS`, `Exception`, `FileResult`, `MEDIA_EXTENSIONS`, `None`, `PATH_PATTERN`, `QueryFn`, `SCANNABLE_FILE_TYPES`, `SENSITIVE_KEYWORDS`, `SOURCE_EXTENSIONS`
- Internal references: `config_loader.py`, `models/state.py`, `tools/filesystem_tools.py`, `utils/strings.py`
- Data sources: None detected.
- Sensitive signals: `age`, `biometric`, `children`, `credit`, `criminal`, `diagnosis`, `disability`, `email`
- Preview note: from __future__ import annotations import csv import json import mimetypes import re from pathlib import Path from typing import Any, Callable from config_loader import load_config from models.state import FileResult...
- Preview coverage: Full preview captured within configured limit.

### `analysis/llm_review.py`

- Type: `source_code`
- Language: `Python`
- Size: `16727` bytes
- Role: llm_review.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: None inferred.
- Schema or fields: `Exception`, `FileResult`, `None`, `QueryFn`, `Question`, `Reason`, `VALID_SEVERITIES`, `VALID_STATUSES`, `WebSearchFn`, `base_result`, `bool`, `chunk_id`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations import json from typing import Any, Callable from analysis.agentic_runtime import run_pydantic_agentic_review from models.state import FileResult, Finding from prompts.loader import...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `analysis/reports.py`

- Type: `source_code`
- Language: `Python`
- Size: `3807` bytes
- Role: reports.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `build_file_report_markdown`, `build_final_report_markdown`
- Schema or fields: `Confidence`, `Explanation`, `Faithfulness`, `Findings`, `Issue`, `Jurisdiction`, `Level`, `Lines`, `Quality`, `Relevancy`, `Remedy`, `Report`
- Internal references: `models/state.py`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from pathlib import Path from models.state import FileResult SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2} def build_file_report_markdown(file_result: FileResult) -> str: findi...
- Preview coverage: Full preview captured within configured limit.

### `analysis/repository_review.py`

- Type: `source_code`
- Language: `Python`
- Size: `24810` bytes
- Role: repository_review.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: None inferred.
- Schema or fields: `Exception`, `None`, `Path`, `SyntaxError`, `_BINARY_DOCUMENT_EXTENSIONS`, `_DEFAULT_EXCLUDED_DIRS`, `_DEFAULT_EXCLUDED_GLOBS`, `_DIRECTORY_PURPOSE_HINTS`, `_METADATA_PREFIX`, `_METADATA_SUFFIX`, `_PRINTABLE_RATIO_MIN`, `_STOPWORDS`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`
- Preview note: from __future__ import annotations import ast import hashlib import json import os import re from collections import Counter, defaultdict from datetime import datetime, timezone from pathlib import Path from typing im...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `demo_violations/india_eu_directive_breach/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `13` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 1 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as __all__ for downstream use.
- Top-level symbols: None inferred.
- Schema or fields: `__all__`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: __all__ = []
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/india_eu_unethical_suite/README.md`

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

### `demo_violations/india_eu_unethical_suite/config/policy_bypass.yaml`

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

### `demo_violations/india_eu_unethical_suite/data/candidates_sensitive.csv`

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

### `demo_violations/india_eu_unethical_suite/data/citizen_scoring.csv`

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

### `demo_violations/india_eu_unethical_suite/data/release_plan.csv`

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

### `demo_violations/india_eu_unethical_suite/data/surveillance_feed.csv`

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

### `demo_violations/india_eu_unethical_suite/docs/violations_map.md`

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

### `demo_violations/india_eu_unethical_suite/src/__init__.py`

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

### `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`

- Type: `source_code`
- Language: `Python`
- Size: `1440` bytes
- Role: biometric_surveillance.py is Python code that appears to implement automated scoring or inference. It exposes 8 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `run_mass_surveillance`
- Schema or fields: `FEED_FILE`, `ONLY`, `__name__`, `alerts`, `encoding`, `handle`, `reader`, `risk`
- Internal references: `demo_violations/india_eu_unethical_suite/src/settings.py`
- Data sources: None detected.
- Sensitive signals: `biometric`, `ethnicity`, `location`, `religion`
- Preview note: """TEST-ONLY: intentionally invasive biometric surveillance simulation.""" import csv from pathlib import Path from .settings import POLICY FEED_FILE = Path(__file__).resolve().parent.parent / "data" / "surveillance_f...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`

- Type: `source_code`
- Language: `Python`
- Size: `1308` bytes
- Role: deepfake_campaign.py is Python code that appears to implement application logic. It exposes 10 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as PLAN_FILE, __name__, disclosure, else, encoding for downstream use.
- Top-level symbols: `schedule_release`
- Schema or fields: `PLAN_FILE`, `__name__`, `disclosure`, `else`, `encoding`, `handle`, `label`, `reader`, `scheduled`, `status`
- Internal references: `demo_violations/india_eu_unethical_suite/src/settings.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: import csv from pathlib import Path from .settings import POLICY PLAN_FILE = Path(__file__).resolve().parent.parent / "data" / "release_plan.csv" def schedule_release() -> list[dict]: scheduled: list[dict] = [] with P...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`

- Type: `source_code`
- Language: `Python`
- Size: `2037` bytes
- Role: hiring_bias_engine.py is Python code that appears to implement automated scoring or inference. It exposes 14 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `rank_candidates`, `auto_hire_or_reject`
- Schema or fields: `DATA_FILE`, `ONLY`, `__name__`, `auto_apply_decisions`, `decisions`, `enable_sensitive_profiling`, `encoding`, `handle`, `item`, `key`, `ranked`, `reader`
- Internal references: `demo_violations/india_eu_unethical_suite/src/settings.py`
- Data sources: None detected.
- Sensitive signals: `disability`, `email`, `gender`, `religion`
- Preview note: """TEST-ONLY: intentionally non-compliant hiring pipeline for scanner evaluation.""" import csv from pathlib import Path from .settings import POLICY DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "cand...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/india_eu_unethical_suite/src/no_oversight_or_redress.py`

- Type: `source_code`
- Language: `Python`
- Size: `618` bytes
- Role: no_oversight_or_redress.py is Python code that appears to implement application logic. It exposes 2 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as __name__, dict for downstream use.
- Top-level symbols: `system_governance_snapshot`
- Schema or fields: `__name__`, `dict`
- Internal references: `demo_violations/india_eu_unethical_suite/src/settings.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from dataclasses import asdict from .settings import POLICY def system_governance_snapshot() -> dict: return { "human_oversight_enabled": not POLICY.skip_human_oversight, "user_notice_enabled": False, "right_to_explan...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/india_eu_unethical_suite/src/run_all.py`

- Type: `source_code`
- Language: `Python`
- Size: `900` bytes
- Role: run_all.py is Python code that appears to implement application logic. It exposes 7 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Campaign, Engine, None, Snapshot, Surveillance for downstream use.
- Top-level symbols: `main`
- Schema or fields: `Campaign`, `Engine`, `None`, `Snapshot`, `Surveillance`, `System`, `__name__`
- Internal references: `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`, `demo_violations/india_eu_unethical_suite/src/no_oversight_or_redress.py`, `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py`
- Data sources: None detected.
- Sensitive signals: `biometric`
- Preview note: """Runs all synthetic non-compliant fixtures and prints their outputs.""" from .biometric_surveillance import run_mass_surveillance from .deepfake_campaign import schedule_release from .hiring_bias_engine import auto_...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/india_eu_unethical_suite/src/settings.py`

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

### `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py`

- Type: `source_code`
- Language: `Python`
- Size: `1557` bytes
- Role: social_scoring_system.py is Python code that appears to implement automated scoring or inference. It exposes 11 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `calculate_social_score`, `assign_entitlements`
- Schema or fields: `ONLY`, `SCORING_FILE`, `__name__`, `encoding`, `float`, `handle`, `outcome`, `outcomes`, `reader`, `record`, `score`
- Internal references: `demo_violations/india_eu_unethical_suite/src/settings.py`
- Data sources: None detected.
- Sensitive signals: `credit`, `political`
- Preview note: """TEST-ONLY: intentionally non-compliant public-sector style social scoring.""" import csv from pathlib import Path from .settings import POLICY SCORING_FILE = Path(__file__).resolve().parent.parent / "data" / "citiz...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/unsafe_hiring_fixture/README.md`

- Type: `document`
- Language: `n/a`
- Size: `520` bytes
- Role: README.md is a text document. Sample: # Synthetic Unsafe Hiring Fixture This directory exists only to validate the compliance scanner. The Python code here intentionally demonstrates an automated...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `disability`, `gender`, `nationality`
- Preview note: # Synthetic Unsafe Hiring Fixture This directory exists only to validate the compliance scanner. The Python code here intentionally demonstrates an automated employment-screening flow that uses protected or sensitive...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/unsafe_hiring_fixture/unsafe_hiring_screen.py`

- Type: `source_code`
- Language: `Python`
- Size: `831` bytes
- Role: unsafe_hiring_screen.py is Python code that appears to implement automated scoring or inference. It exposes 2 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `predict_user_ethnicity`, `analyze_sentiment`, `log_sensitive_data`
- Schema or fields: `analysis`, `data`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `ethnicity`
- Preview note: import random from textblob import TextBlob def predict_user_ethnicity(name): """ Predicts a user's ethnicity based on their name """ if len(name) < 3: return random.choice(["Asian", "Caucasian", "African", "Hispanic"...
- Preview coverage: Full preview captured within configured limit.

### `demo_violations/unsafe_hiring_fixture/data/applicants_sensitive.csv`

- Type: `structured_data`
- Language: `n/a`
- Size: `215` bytes
- Role: applicants_sensitive.csv appears to be structured data with fields such as candidate_id, gender, age, zip_code, disability_status, nationality. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: `candidate_id`, `gender`, `age`, `zip_code`, `disability_status`, `nationality`, `resume_score`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `disability`, `gender`, `nationality`
- Preview note: candidate_id,gender,age,zip_code,disability_status,nationality,resume_score A-1001,female,52,94110,yes,brazil,88 A-1002,male,29,10001,no,us,76 A-1003,female,47,90210,no,india,91 A-1004,non-binary,38,94107,yes,uk,84
- Preview coverage: Full preview captured within configured limit.

### `docs/AGENTS.md`

- Type: `document`
- Language: `n/a`
- Size: `2371` bytes
- Role: AGENTS.md is a text document. Sample: # Repository Guidelines ## Project Structure & Module Organization Core scanner logic lives in `analysis/`, `nodes/`, `graphs/`, and `models/`. Integration l...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: # Repository Guidelines ## Project Structure & Module Organization Core scanner logic lives in `analysis/`, `nodes/`, `graphs/`, and `models/`. Integration layers live in `llm/`, `rag/`, `tools/`, `tracing/`, and `ui/...
- Preview coverage: Full preview captured within configured limit.

### `docs/ARCHITECTURE.md`

- Type: `document`
- Language: `n/a`
- Size: `23248` bytes
- Role: ARCHITECTURE.md is a text document. Sample: # AI Ethics Compliance Agent Architecture ## 1. System Identity The current system is a VS Code-first, real-time AI ethics reviewer for local repositories. I...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`
- Preview note: # AI Ethics Compliance Agent Architecture ## 1. System Identity The current system is a VS Code-first, real-time AI ethics reviewer for local repositories. It is built around five ideas: 1. The editor is the user inte...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `docs/EXTENSION_PUBLISH.md`

- Type: `document`
- Language: `n/a`
- Size: `7904` bytes
- Role: EXTENSION_PUBLISH.md is a text document. Sample: # Publishing AI Ethics Extension ## Part 1: Publishing Without API Keys ### Step 1: Prepare the Release ```bash # From the repository root cd /Users/aishik/D...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: `https://marketplace.visualstudio.com/`, `https://console.groq.com/keys`, `https://openrouter.ai/keys`, `https://ollama.ai/keys`, `http://localhost:11434``
- Sensitive signals: `age`, `minor`
- Preview note: # Publishing AI Ethics Extension ## Part 1: Publishing Without API Keys ### Step 1: Prepare the Release ```bash # From the repository root cd /Users/aishik/Documents/Programming/ethics_agent # Verify your .env file is...
- Preview coverage: Full preview captured within configured limit.

### `docs/PRD_ui.md`

- Type: `document`
- Language: `n/a`
- Size: `55249` bytes
- Role: PRD_ui.md is a text document. Sample: # AI Ethics Compliance Agent ## Product Requirements Document — v4.0 _April 2026 · Status: DRAFT · Priority: P0_ --- ## Table of Contents 1. [Executive Summa...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`, `race`
- Preview note: # AI Ethics Compliance Agent ## Product Requirements Document — v4.0 _April 2026 · Status: DRAFT · Priority: P0_ --- ## Table of Contents 1. [Executive Summary](#1-executive-summary) 2. [Goals & Non-Goals](#2-goals--n...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `docs/PRD_vscode_extension.md`

- Type: `document`
- Language: `n/a`
- Size: `59917` bytes
- Role: PRD_vscode_extension.md is a text document. Sample: # AI Ethics Compliance Agent ## Product Requirements Document — v4.0 _April 2026 · Status: DRAFT · Priority: P0_ --- ## Table of Contents 1. [Executive Summa...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`
- Preview note: # AI Ethics Compliance Agent ## Product Requirements Document — v4.0 _April 2026 · Status: DRAFT · Priority: P0_ --- ## Table of Contents 1. [Executive Summary](#1-executive-summary) 2. [Goals & Non-Goals](#2-goals--n...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `graphs/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `56` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """LangGraph graph builders for the compliance scan."""
- Preview coverage: Full preview captured within configured limit.

### `graphs/checkpointer.py`

- Type: `source_code`
- Language: `Python`
- Size: `2102` bytes
- Role: checkpointer.py is Python code that appears to implement application logic. It exposes 20 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as CHECKPOINT_BACKEND, Exception, None, _SAVER_CACHE, backend for downstream use.
- Top-level symbols: `get_checkpointer`, `list_checkpoint_thread_ids`
- Schema or fields: `CHECKPOINT_BACKEND`, `Exception`, `None`, `_SAVER_CACHE`, `backend`, `check_same_thread`, `checkpoint_config`, `config`, `connection`, `cursor`, `effective`, `journal_mode`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations import os import sqlite3 from pathlib import Path from typing import Any _SAVER_CACHE: dict[str, Any] = {} def get_checkpointer(config: dict[str, Any] | None = None): effective = con...
- Preview coverage: Full preview captured within configured limit.

### `graphs/compliance_graph.py`

- Type: `source_code`
- Language: `Python`
- Size: `1211` bytes
- Role: compliance_graph.py is Python code that appears to implement application logic. It exposes 6 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as None, StateGraph, active_checkpointer, builder, checkpointer for downstream use.
- Top-level symbols: `build_compliance_graph`, `compile_graph`
- Schema or fields: `None`, `StateGraph`, `active_checkpointer`, `builder`, `checkpointer`, `config`
- Internal references: `graphs/checkpointer.py`, `models/state.py`, `nodes/initialize.py`, `nodes/review_file.py`, `nodes/review_repository.py`, `nodes/write_report.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations from langgraph.graph import END, START, StateGraph from graphs.checkpointer import get_checkpointer from models.state import ComplianceState from nodes.initialize import initialize_n...
- Preview coverage: Full preview captured within configured limit.

### `graphs/file_review_subgraph.py`

- Type: `source_code`
- Language: `Python`
- Size: `517` bytes
- Role: file_review_subgraph.py is Python code that appears to implement application logic. It exposes 4 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as content, model, prompt, tools for downstream use.
- Top-level symbols: `build_file_review_agent`
- Schema or fields: `content`, `model`, `prompt`, `tools`
- Internal references: `prompts/loader.py`, `tools/filesystem_tools.py`, `tools/rag_tool.py`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from langchain_core.messages import SystemMessage from langgraph.prebuilt import create_react_agent from prompts.loader import load_prompt from tools.filesystem_tools import read_fil...
- Preview coverage: Full preview captured within configured limit.

### `knowledge/ai_ethics_knowledge_base.pdf`

- Type: `document`
- Language: `n/a`
- Size: `436279` bytes
- Role: ai_ethics_knowledge_base.pdf is a text document. Sample: 
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: Binary, media, or non-text content.
- Preview coverage: Full preview captured within configured limit.

### `llm/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `48` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """LLM provider factory and related helpers."""
- Preview coverage: Full preview captured within configured limit.

### `llm/provider_factory.py`

- Type: `source_code`
- Language: `Python`
- Size: `6106` bytes
- Role: provider_factory.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 4 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, _KNOWN_PROVIDERS, _LLM_CACHE, api_key for downstream use.
- Top-level symbols: `_make_rate_limiter`, `provider_requires_api_key`, `missing_provider_credential`, `list_local_ollama_models`, `get_available_models`, `resolve_provider_model`, `create_llm`, `try_create_llm`
- Schema or fields: `Exception`, `None`, `_KNOWN_PROVIDERS`, `_LLM_CACHE`, `api_key`, `available_models`, `base_url`, `cache_key`, `capture_output`, `check`, `config`, `configured_default_model`
- Internal references: `config_loader.py`
- Data sources: `https://cloud.ollama.com`, `https://openrouter.ai/api/v1`, `https://local.ai-ethics-agent`, `http://localhost:11434`
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations import os import subprocess from typing import Any from config_loader import load_config _LLM_CACHE: dict[tuple[str, str, str], Any] = {} _KNOWN_PROVIDERS = ("ollama_cloud", "openrou...
- Preview coverage: Full preview captured within configured limit.

### `models/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `53` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Typed models used across the compliance graph."""
- Preview coverage: Full preview captured within configured limit.

### `models/events.py`

- Type: `source_code`
- Language: `Python`
- Size: `494` bytes
- Role: events.py is Python code that appears to implement application logic. It exposes 6 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as event_type, extra, file_path, message, payload for downstream use.
- Top-level symbols: `now_iso`, `progress_event`
- Schema or fields: `event_type`, `extra`, `file_path`, `message`, `payload`, `str`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from datetime import datetime, timezone from typing import Any def now_iso() -> str: return datetime.now(timezone.utc).isoformat() def progress_event(event_type: str, file_path: str...
- Preview coverage: Full preview captured within configured limit.

### `models/state.py`

- Type: `source_code`
- Language: `Python`
- Size: `1959` bytes
- Role: state.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `AgenticGrade`, `RetrievalEvidence`, `WebSearchEvidence`, `Finding`, `FileResult`, `ProgressEvent`, `ComplianceState`
- Schema or fields: `agentic_context`, `agentic_grade`, `answer`, `chunk_id`, `confidence`, `config`, `context_quality`, `directory_analysis_path`, `end_line`, `error`, `event_type`, `explanation`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations import operator from typing import Annotated, Any from typing_extensions import NotRequired, TypedDict class AgenticGrade(TypedDict): relevancy: float faithfulness: float context_qua...
- Preview coverage: Full preview captured within configured limit.

### `nodes/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `34` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Graph node implementations."""
- Preview coverage: Full preview captured within configured limit.

### `nodes/initialize.py`

- Type: `source_code`
- Language: `Python`
- Size: `714` bytes
- Role: initialize.py is Python code that appears to implement application logic. It exposes 8 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as dict, file_path, for, message, name for downstream use.
- Top-level symbols: `initialize_node`
- Schema or fields: `dict`, `file_path`, `for`, `message`, `name`, `output_dir`, `state`, `tags`
- Internal references: `models/events.py`, `models/state.py`, `tools/filesystem_tools.py`, `utils/compat.py`, `nodes/write_report.py`
- Data sources: None detected.
- Sensitive signals: `age`, `race`
- Preview note: from __future__ import annotations from models.events import progress_event from models.state import ComplianceState from tools.filesystem_tools import safe_mkdir from utils.compat import traceable from .write_report...
- Preview coverage: Full preview captured within configured limit.

### `nodes/review_file.py`

- Type: `source_code`
- Language: `Python`
- Size: `6729` bytes
- Role: review_file.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `_rag_query`, `_apply_line_offset`, `_llm_required_error`, `review_file_node`
- Schema or fields: `Completed`, `FileResult`, `None`, `Reason`, `Reviewing`, `agentic_grade`, `base_result`, `complete_event`, `config`, `default`, `dict`, `else`
- Internal references: `analysis/core.py`, `analysis/llm_review.py`, `llm/provider_factory.py`, `models/events.py`, `models/state.py`, `rag/retriever.py`, `tools/web_search_tool.py`, `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `age`, `race`
- Preview note: from __future__ import annotations import os from typing import Any from langchain_core.callbacks.manager import dispatch_custom_event from langchain_core.runnables import RunnableConfig from analysis.core import anal...
- Preview coverage: Full preview captured within configured limit.

### `nodes/review_repository.py`

- Type: `source_code`
- Language: `Python`
- Size: `2253` bytes
- Role: review_repository.py is Python code that appears to implement application logic. It exposes 16 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as analysis, complete_event, config, dict, error_event for downstream use.
- Top-level symbols: `review_repository_node`
- Schema or fields: `analysis`, `complete_event`, `config`, `dict`, `error_event`, `exc`, `failed`, `file_path`, `force`, `message`, `name`, `payload`
- Internal references: `analysis/repository_review.py`, `models/events.py`, `models/state.py`, `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `age`, `race`
- Preview note: from __future__ import annotations from langchain_core.callbacks.manager import dispatch_custom_event from langchain_core.runnables import RunnableConfig from analysis.repository_review import ensure_directory_analysi...
- Preview coverage: Full preview captured within configured limit.

### `nodes/write_report.py`

- Type: `source_code`
- Language: `Python`
- Size: `1863` bytes
- Role: write_report.py is Python code that appears to implement application logic. It exposes 18 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as None, Path, candidate, config, dict for downstream use.
- Top-level symbols: `resolve_workspace_root`, `resolve_output_dir`, `write_report_node`
- Schema or fields: `None`, `Path`, `candidate`, `config`, `dict`, `event`, `file_path`, `lock_timeout`, `markdown`, `message`, `name`, `output_dir`
- Internal references: `analysis/core.py`, `analysis/reports.py`, `models/events.py`, `models/state.py`, `tools/filesystem_tools.py`, `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `age`, `race`
- Preview note: from __future__ import annotations from pathlib import Path from analysis.core import report_filename_for from analysis.reports import build_file_report_markdown from models.events import progress_event from models.st...
- Preview coverage: Full preview captured within configured limit.

### `prompts/file_reviewer.md`

- Type: `document`
- Language: `n/a`
- Size: `4218` bytes
- Role: file_reviewer.md is a text document. Sample: # File Reviewer System Prompt You are the final compliance reviewer for one repository file or one incremental file snippet inside an AI ethics compliance sc...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: # File Reviewer System Prompt You are the final compliance reviewer for one repository file or one incremental file snippet inside an AI ethics compliance scanner. Your job is to determine: - what the file does, - wha...
- Preview coverage: Full preview captured within configured limit.

### `prompts/loader.py`

- Type: `source_code`
- Language: `Python`
- Size: `397` bytes
- Role: loader.py is Python code that appears to implement application logic. It exposes 7 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as PROMPTS_DIR, encoding, found, maxsize, name for downstream use.
- Top-level symbols: `load_prompt`
- Schema or fields: `PROMPTS_DIR`, `encoding`, `found`, `maxsize`, `name`, `prompt_path`, `str`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations from functools import lru_cache from pathlib import Path PROMPTS_DIR = Path(__file__).resolve().parent @lru_cache(maxsize=16) def load_prompt(name: str) -> str: prompt_path = PROMPTS...
- Preview coverage: Full preview captured within configured limit.

### `rag/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `43` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """RAG ingestion and retrieval helpers."""
- Preview coverage: Full preview captured within configured limit.

### `rag/ingestor.py`

- Type: `source_code`
- Language: `Python`
- Size: `5162` bytes
- Role: ingestor.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, Path, SECTION_PATTERNS, archived for downstream use.
- Top-level symbols: `_guess_section`, `_guess_jurisdiction`, `_resolve_pdf_path`, `_create_splitter`, `needs_ingestion`, `ingest`
- Schema or fields: `Exception`, `None`, `Path`, `SECTION_PATTERNS`, `archived`, `bool`, `chunk_id`, `chunk_overlap`, `chunk_size`, `chunks`, `collection`, `collection_name`
- Internal references: `config_loader.py`, `rag/storage.py`, `utils/compat.py`, `rag/retriever.py`
- Data sources: None detected.
- Sensitive signals: `age`, `race`, `union`
- Preview note: from __future__ import annotations import re from datetime import datetime, timezone from pathlib import Path from typing import Any import fitz from config_loader import load_config from rag.storage import create_per...
- Preview coverage: Full preview captured within configured limit.

### `rag/retriever.py`

- Type: `source_code`
- Language: `Python`
- Size: `8673` bytes
- Role: retriever.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `HashingEmbeddings`, `_create_embeddings`, `_tokenize`, `_expand_query`, `_confidence_from_distance`, `_trust_score`, `_dedupe_key`, `Retriever`
- Schema or fields: `Exception`, `HashingEmbeddings`, `None`, `QUERY_EXPANSIONS`, `REGULATORY_TERMS`, `Retriever`, `_instances`, `agentic_config`, `bool`, `candidates`, `chunk`, `chunk_id`
- Internal references: `config_loader.py`, `rag/storage.py`, `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `age`, `biometric`, `face`, `fingerprint`, `race`
- Preview note: from __future__ import annotations import math import re from collections import OrderedDict from typing import Any from config_loader import load_config from rag.storage import create_persistent_client from utils.com...
- Preview coverage: Full preview captured within configured limit.

### `rag/storage.py`

- Type: `source_code`
- Language: `Python`
- Size: `1335` bytes
- Role: storage.py is Python code that appears to implement application logic. It exposes 11 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, archived, client, else for downstream use.
- Top-level symbols: `_validate_client`, `create_persistent_client`, `archive_persist_dir`, `create_persistent_client_with_recovery`
- Schema or fields: `Exception`, `None`, `archived`, `client`, `else`, `heartbeat`, `path`, `persist_dir`, `source`, `timestamp`, `try`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations import shutil from datetime import datetime, timezone from pathlib import Path from typing import Any import chromadb from chromadb.api.shared_system_client import SharedSystemClient...
- Preview coverage: Full preview captured within configured limit.

### `scripts/ingest_knowledge_base.py`

- Type: `source_code`
- Language: `Python`
- Size: `2008` bytes
- Role: ingest_knowledge_base.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `parse_args`, `main`
- Schema or fields: `DEFAULT_PROBE_QUERY`, `Exception`, `Namespace`, `None`, `REPO_ROOT`, `__name__`, `args`, `chunk`, `confidence`, `config`, `count`, `default`
- Internal references: `config_loader.py`, `rag/ingestor.py`, `rag/retriever.py`
- Data sources: None detected.
- Sensitive signals: `age`, `gender`
- Preview note: #!/usr/bin/env python3 from __future__ import annotations import argparse import os import sys from pathlib import Path REPO_ROOT = Path(__file__).resolve().parents[1] if str(REPO_ROOT) not in sys.path: sys.path.inser...
- Preview coverage: Full preview captured within configured limit.

### `scripts/verify_demo_scan.py`

- Type: `source_code`
- Language: `Python`
- Size: `3794` bytes
- Role: verify_demo_scan.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as DEFAULT_QUERY, DEFAULT_TARGET, Exception, Namespace, None for downstream use.
- Top-level symbols: `parse_args`, `main`
- Schema or fields: `DEFAULT_QUERY`, `DEFAULT_TARGET`, `Exception`, `Namespace`, `None`, `REPO_ROOT`, `Remedy`, `Status`, `Summary`, `__name__`, `action`, `args`
- Internal references: `config_loader.py`, `graphs/compliance_graph.py`, `rag/ingestor.py`, `rag/retriever.py`, `tracing/langsmith_setup.py`
- Data sources: None detected.
- Sensitive signals: `age`, `gender`
- Preview note: #!/usr/bin/env python3 from __future__ import annotations import argparse import os import sys import uuid from pathlib import Path REPO_ROOT = Path(__file__).resolve().parents[1] if str(REPO_ROOT) not in sys.path: sy...
- Preview coverage: Full preview captured within configured limit.

### `tests/conftest.py`

- Type: `source_code`
- Language: `Python`
- Size: `195` bytes
- Role: conftest.py is Python code that appears to implement application logic. It exposes 2 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as REPO_ROOT, path for downstream use.
- Top-level symbols: None inferred.
- Schema or fields: `REPO_ROOT`, `path`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations import sys from pathlib import Path REPO_ROOT = Path(__file__).resolve().parents[1] if str(REPO_ROOT) not in sys.path: sys.path.insert(0, str(REPO_ROOT))
- Preview coverage: Full preview captured within configured limit.

### `tests/test_analysis_core.py`

- Type: `source_code`
- Language: `Python`
- Size: `2203` bytes
- Role: test_analysis_core.py is Python code that appears to implement model training, automated scoring or inference. It exposes 15 recognizable fields and 2 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `test_extract_data_sources_finds_urls_and_local_paths`, `test_analyze_file_prepares_review_metadata_without_heuristic_findings`, `test_analyze_file_skips_directory_analysis_artifact`, `test_analyze_file_skips_non_target_config_files`
- Schema or fields: `None`, `applicants`, `config`, `content`, `dataset`, `encoding`, `features`, `file_content`, `file_path`, `https`, `model`, `napi`
- Internal references: `analysis/core.py`
- Data sources: `https://example.com/data`, `./data/applicants.csv`
- Sensitive signals: `age`, `gender`
- Preview note: from __future__ import annotations from pathlib import Path from analysis.core import analyze_file, extract_data_sources def test_extract_data_sources_finds_urls_and_local_paths() -> None: content = 'dataset = "./data...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_config_loader.py`

- Type: `source_code`
- Language: `Python`
- Size: `1476` bytes
- Role: test_config_loader.py is Python code that appears to implement application logic. It exposes 10 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as None, config, config_path, default_provider, encoding for downstream use.
- Top-level symbols: `test_load_config_adds_prd_defaults`, `test_load_config_defaults_to_repo_root_when_relative_path_is_missing`
- Schema or fields: `None`, `config`, `config_path`, `default_provider`, `encoding`, `knowledge`, `llm`, `pdf_path`, `plus`, `tmp_path`
- Internal references: `config_loader.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations from pathlib import Path from config_loader import load_config def test_load_config_adds_prd_defaults(tmp_path: Path) -> None: config_path = tmp_path / "config.yaml" config_path.writ...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_filesystem_tools.py`

- Type: `source_code`
- Language: `Python`
- Size: `617` bytes
- Role: test_filesystem_tools.py is Python code that appears to implement application logic. It exposes 6 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as None, allowed_root, content, file, file_path for downstream use.
- Top-level symbols: `test_safe_resolve_path_rejects_path_traversal`, `test_read_text_file_returns_binary_placeholder`
- Schema or fields: `None`, `allowed_root`, `content`, `file`, `file_path`, `tmp_path`
- Internal references: `tools/filesystem_tools.py`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from pathlib import Path import pytest from tools.filesystem_tools import read_text_file, safe_resolve_path def test_safe_resolve_path_rejects_path_traversal(tmp_path: Path) -> None:...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_graph_streaming.py`

- Type: `source_code`
- Language: `Python`
- Size: `5928` bytes
- Role: test_graph_streaming.py is Python code that appears to implement model training, automated scoring or inference. It exposes 17 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `_stub_llm_review`, `test_graph_streams_violation_events_and_writes_report`, `test_graph_applies_line_offset_to_incremental_snippets`
- Schema or fields: `None`, `checkpointer`, `config`, `encoding`, `events`, `features`, `file_path`, `findings`, `graph`, `initial_state`, `output`, `plus`
- Internal references: `graphs/compliance_graph.py`, `nodes/review_file.py`
- Data sources: None detected.
- Sensitive signals: `age`, `gender`
- Preview note: from __future__ import annotations import asyncio import json from pathlib import Path from graphs.compliance_graph import compile_graph import nodes.review_file as review_file_module def _stub_llm_review(monkeypatch)...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_llm_review.py`

- Type: `source_code`
- Language: `Python`
- Size: `6181` bytes
- Role: test_llm_review.py is Python code that appears to implement model training, automated scoring or inference. It exposes 28 recognizable fields and 1 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `FakeLLM`, `_base_result`, `test_assess_file_with_llm_runs_web_augmentation_when_needed`, `test_assess_file_with_llm_returns_error_when_model_response_is_invalid`, `test_assess_file_with_llm_includes_repository_analysis_context`
- Schema or fields: `FakeLLM`, `None`, `Purpose`, `_responses`, `base_result`, `config`, `description`, `dict`, `file_content`, `file_path`, `https`, `llm`
- Internal references: `analysis/llm_review.py`
- Data sources: `https://example.org/guidance`
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from analysis.llm_review import assess_file_with_llm class FakeLLM: def __init__(self, responses: list[str]): self._responses = list(responses) self.prompts: list[str] = [] def invok...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_mcp_server.py`

- Type: `source_code`
- Language: `Python`
- Size: `3407` bytes
- Role: test_mcp_server.py is Python code that appears to implement model training, automated scoring or inference. It exposes 15 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `test_stream_compliance_check_yields_custom_and_completion_events`, `test_ensure_runtime_logs_and_continues_when_rag_fails`
- Schema or fields: `None`, `captured`, `checkpointer`, `config`, `encoding`, `events`, `features`, `file_content`, `file_path`, `graph`, `model`, `plus`
- Internal references: `mcp_server.py`, `nodes/review_file.py`, `graphs/compliance_graph.py`
- Data sources: None detected.
- Sensitive signals: `age`, `gender`
- Preview note: from __future__ import annotations import asyncio from pathlib import Path import mcp_server import nodes.review_file as review_file_module from graphs.compliance_graph import compile_graph from mcp_server import _ens...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_provider_factory.py`

- Type: `source_code`
- Language: `Python`
- Size: `1757` bytes
- Role: test_provider_factory.py is Python code that appears to implement application logic. It exposes 6 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as None, config, model, plus, provider for downstream use.
- Top-level symbols: `test_resolve_provider_model_falls_back_from_invalid_requested_model`, `test_resolve_provider_model_falls_back_from_unknown_provider`, `test_missing_provider_credential_returns_required_env_name`, `test_missing_provider_credential_returns_none_when_env_present`
- Schema or fields: `None`, `config`, `model`, `plus`, `provider`, `raising`
- Internal references: `llm/provider_factory.py`
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations from llm.provider_factory import missing_provider_credential, resolve_provider_model def test_resolve_provider_model_falls_back_from_invalid_requested_model() -> None: provider, mode...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_rag_storage.py`

- Type: `source_code`
- Language: `Python`
- Size: `2419` bytes
- Role: test_rag_storage.py is Python code that appears to implement application logic. It exposes 13 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as DummyClient, DummyCollection, None, archived, archived_dir for downstream use.
- Top-level symbols: `test_create_persistent_client_with_recovery_archives_and_retries`, `test_needs_ingestion_returns_true_after_recovery`, `test_needs_ingestion_returns_false_for_populated_collection`
- Schema or fields: `DummyClient`, `DummyCollection`, `None`, `archived`, `archived_dir`, `calls`, `client`, `collection`, `int`, `name`, `path`, `persist_dir`
- Internal references: `rag/ingestor.py`, `rag/storage.py`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations from pathlib import Path import rag.ingestor as ingestor import rag.storage as storage def test_create_persistent_client_with_recovery_archives_and_retries(monkeypatch, tmp_path: Pat...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_reports.py`

- Type: `source_code`
- Language: `Python`
- Size: `2311` bytes
- Role: test_reports.py is Python code that appears to implement model training, automated scoring or inference. It exposes 4 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `test_build_file_report_markdown_matches_prd_sections`
- Schema or fields: `None`, `Remedy`, `Report`, `markdown`
- Internal references: `analysis/reports.py`
- Data sources: None detected.
- Sensitive signals: `age`, `gender`
- Preview note: from __future__ import annotations from analysis.reports import build_file_report_markdown def test_build_file_report_markdown_matches_prd_sections() -> None: markdown = build_file_report_markdown( { "file_path": "/tm...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_repository_review.py`

- Type: `source_code`
- Language: `Python`
- Size: `2397` bytes
- Role: test_repository_review.py is Python code that appears to implement automated scoring or inference. It exposes 12 recognizable fields and 1 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `test_ensure_directory_analysis_creates_markdown_and_skips_ignored_paths`, `test_ensure_directory_analysis_reuses_existing_file_and_refreshes_on_repo_change`
- Schema or fields: `None`, `SECRET_TOKEN`, `analysis_path`, `config`, `encoding`, `first`, `home`, `model`, `result`, `second`, `third`, `tmp_path`
- Internal references: `analysis/repository_review.py`
- Data sources: `data/records.csv`
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations from pathlib import Path from analysis.repository_review import ensure_directory_analysis def test_ensure_directory_analysis_creates_markdown_and_skips_ignored_paths(tmp_path: Path)...
- Preview coverage: Full preview captured within configured limit.

### `tests/test_review_file_node.py`

- Type: `source_code`
- Language: `Python`
- Size: `1163` bytes
- Role: test_review_file_node.py is Python code that appears to implement model training. It exposes 9 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely trains or fine-tunes a model artifact for later deployment.
- Top-level symbols: `test_review_file_node_returns_actionable_error_for_missing_provider_key`
- Schema or fields: `None`, `config`, `file_result`, `kwargs`, `plus`, `raising`, `result`, `state`, `top_k`
- Internal references: `nodes/review_file.py`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: from __future__ import annotations import nodes.review_file as review_file_module def test_review_file_node_returns_actionable_error_for_missing_provider_key(monkeypatch) -> None: monkeypatch.delenv("OPENROUTER_API_KE...
- Preview coverage: Full preview captured within configured limit.

### `tools/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `58` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: """Tool modules exposed to LangGraph agents and nodes."""
- Preview coverage: Full preview captured within configured limit.

### `tools/filesystem_tools.py`

- Type: `source_code`
- Language: `Python`
- Size: `3859` bytes
- Role: filesystem_tools.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, Path, allowed_root, chardet for downstream use.
- Top-level symbols: `_safe_path`, `safe_resolve_path`, `safe_mkdir`, `_detect_encoding`, `read_text_file`, `read_file_tool`, `write_text_file`, `write_file_tool`
- Schema or fields: `Exception`, `None`, `Path`, `allowed_root`, `chardet`, `content`, `detected`, `dir`, `directory`, `encoding`, `end_line`, `errors`
- Internal references: `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `race`
- Preview note: from __future__ import annotations import os import shutil import tempfile from pathlib import Path from typing import Optional try: from langchain.tools import tool except Exception: # pragma: no cover from utils.com...
- Preview coverage: Full preview captured within configured limit.

### `tools/rag_tool.py`

- Type: `source_code`
- Language: `Python`
- Size: `644` bytes
- Role: rag_tool.py is Python code that appears to implement application logic. It exposes 12 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, description, expand_query, int for downstream use.
- Top-level symbols: `query_rag_tool`
- Schema or fields: `Exception`, `None`, `description`, `expand_query`, `int`, `min_trust`, `name`, `pragma`, `retriever`, `tags`, `top_k`, `try`
- Internal references: `config_loader.py`, `rag/retriever.py`, `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `race`
- Preview note: from __future__ import annotations from typing import Any try: from langchain.tools import tool except Exception: # pragma: no cover from utils.compat import tool from config_loader import load_config from rag.retriev...
- Preview coverage: Full preview captured within configured limit.

### `tools/web_search_tool.py`

- Type: `source_code`
- Language: `Python`
- Size: `1813` bytes
- Role: web_search_tool.py is Python code that appears to implement application logic. It exposes 22 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, TAVILY_API_KEY, api_key, bool for downstream use.
- Top-level symbols: `_truthy`, `_normalized_tavily_api_key`, `web_search_tool`
- Schema or fields: `Exception`, `None`, `TAVILY_API_KEY`, `api_key`, `bool`, `client`, `ddgs`, `int`, `max`, `max_results`, `min`, `multiplier`
- Internal references: `utils/compat.py`
- Data sources: None detected.
- Sensitive signals: `race`
- Preview note: from __future__ import annotations import os from typing import Any from utils.compat import tool, traceable try: from tenacity import retry, stop_after_attempt, wait_exponential except Exception: # pragma: no cover -...
- Preview coverage: Full preview captured within configured limit.

### `tracing/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `53` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Tracing helpers for LangSmith-aware execution."""
- Preview coverage: Full preview captured within configured limit.

### `tracing/langsmith_setup.py`

- Type: `source_code`
- Language: `Python`
- Size: `1590` bytes
- Role: langsmith_setup.py is Python code that appears to implement application logic. It exposes 17 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, None, bool, callbacks, client for downstream use.
- Top-level symbols: `_tracing_enabled`, `get_langsmith_tracer`, `get_run_config`, `resolve_run_url`
- Schema or fields: `Exception`, `None`, `bool`, `callbacks`, `client`, `file_path`, `flag`, `model`, `project`, `project_name`, `provider`, `run`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `race`
- Preview note: from __future__ import annotations import os from typing import Any from langsmith import Client def _tracing_enabled() -> bool: if not os.getenv("LANGSMITH_API_KEY"): return False flag = os.getenv("LANGSMITH_TRACING_...
- Preview coverage: Full preview captured within configured limit.

### `utils/__init__.py`

- Type: `source_code`
- Language: `Python`
- Size: `76` bytes
- Role: __init__.py is Python code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: """Utility helpers for optional integrations and small shared functions."""
- Preview coverage: Full preview captured within configured limit.

### `utils/compat.py`

- Type: `source_code`
- Language: `Python`
- Size: `1469` bytes
- Role: compat.py is Python code that appears to implement application logic. It exposes 7 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Exception, args, bound, func, kwargs for downstream use.
- Top-level symbols: `_passthrough_decorator`, `tool`, `traceable`, `get_runnable_config_type`, `get_tool_exception_type`
- Schema or fields: `Exception`, `args`, `bound`, `func`, `kwargs`, `try`, `type`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `race`
- Preview note: from __future__ import annotations from functools import wraps from typing import Any, Callable, TypeVar F = TypeVar("F", bound=Callable[..., Any]) def _passthrough_decorator(func: F) -> F: @wraps(func) def wrapped(*a...
- Preview coverage: Full preview captured within configured limit.

### `utils/strings.py`

- Type: `source_code`
- Language: `Python`
- Size: `1026` bytes
- Role: strings.py is Python code that appears to implement application logic. It exposes 15 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as JSONDecodeError, None, RESULT_PATTERNS, candidate, cleaned for downstream use.
- Top-level symbols: `extract_tagged_json`, `slugify_filename`, `shorten`
- Schema or fields: `JSONDecodeError`, `None`, `RESULT_PATTERNS`, `candidate`, `cleaned`, `int`, `limit`, `match`, `parsed`, `payload`, `sanitized`, `str`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: from __future__ import annotations import json import re from typing import Any RESULT_PATTERNS = ( re.compile(r"<RESULT>(.*?)</RESULT>", re.DOTALL | re.IGNORECASE), re.compile(r"<r>(.*?)</r>", re.DOTALL | re.IGNORECA...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/CHANGELOG.md`

- Type: `document`
- Language: `n/a`
- Size: `633` bytes
- Role: CHANGELOG.md is a text document. Sample: # Changelog All notable changes to the AI Ethics Compliance Agent extension will be documented in this file. ## [Unreleased] - Work in progress. ## [0.1.0] -...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: # Changelog All notable changes to the AI Ethics Compliance Agent extension will be documented in this file. ## [Unreleased] - Work in progress. ## [0.1.0] - 2026-04-04 ### Added - Initial release of the AI Ethics Com...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/README.md`

- Type: `document`
- Language: `n/a`
- Size: `3456` bytes
- Role: README.md is a text document. Sample: # VS Code Extension Runbook This package is the VS Code frontend for the AI Ethics Compliance Agent. It starts the Python MCP server as a subprocess, sends t...
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`
- Preview note: # VS Code Extension Runbook This package is the VS Code frontend for the AI Ethics Compliance Agent. It starts the Python MCP server as a subprocess, sends the active file to `check_file`, and renders streamed finding...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/install_extension_locally.sh`

- Type: `source_code`
- Language: `Shell`
- Size: `93` bytes
- Role: install_extension_locally.sh is Shell code that appears to implement application logic. It exposes 0 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file appears to implement logic that transforms inputs into derived outputs.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: #!/bin/bash npm run compile && code --install-extension ai-ethics-compliance-agent-0.1.0.vsix
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/package-lock.json`

- Type: `structured_data`
- Language: `n/a`
- Size: `41941` bytes
- Role: package-lock.json appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: `https://registry.npmjs.org/@hono/node-server/-/node-server-1.19.12.tgz`, `https://registry.npmjs.org/@modelcontextprotocol/sdk/-/sdk-1.29.0.tgz`, `https://registry.npmjs.org/@types/node/-/node-20.19.37.tgz`, `https://registry.npmjs.org/@types/vscode/-/vscode-1.110.0.tgz`, `https://registry.npmjs.org/accepts/-/accepts-2.0.0.tgz`, `https://registry.npmjs.org/ajv/-/ajv-8.18.0.tgz`, `https://github.com/sponsors/epoberezkin`, `https://registry.npmjs.org/ajv-formats/-/ajv-formats-3.0.1.tgz`
- Sensitive signals: `age`
- Preview note: { "name": "ai-ethics-compliance-agent", "version": "0.1.0", "lockfileVersion": 3, "requires": true, "packages": { "": { "name": "ai-ethics-compliance-agent", "version": "0.1.0", "dependencies": { "@modelcontextprotoco...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `vscode-extension/package.json`

- Type: `structured_data`
- Language: `n/a`
- Size: `3175` bytes
- Role: package.json appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: { "name": "ai-ethics-compliance-agent", "displayName": "AI Ethics Compliance Agent", "description": "Real-time AI ethics compliance diagnostics backed by a Python LangGraph MCP server.", "version": "0.1.0", "publisher...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/tsconfig.json`

- Type: `structured_data`
- Language: `n/a`
- Size: `377` bytes
- Role: tsconfig.json appears to be structured data with fields such as unknown columns. This summary is structural context for the LLM review.
- Objective/output: No concrete output inferred.
- Top-level symbols: None inferred.
- Schema or fields: None inferred.
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: None inferred from preview.
- Preview note: { "compilerOptions": { "module": "commonjs", "target": "ES2022", "lib": [ "ES2022" ], "outDir": "out", "rootDir": "src", "strict": true, "sourceMap": true, "esModuleInterop": true, "moduleResolution": "node", "types":...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/out/diagnostics.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `2980` bytes
- Role: diagnostics.js is JavaScript code that appears to implement application logic. It exposes 26 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Remedy, Source, __createBinding, __esModule, __importStar for downstream use.
- Top-level symbols: `vscode`, `toSeverity`, `findingToDiagnostic`, `lastLine`, `startLine`, `endLine`, `range`, `level`, `message`, `diagnostic`
- Schema or fields: `Remedy`, `Source`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `code`, `desc`, `diagnostic`, `endLine`, `enumerable`, `findingToDiagnostic`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `location`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/out/extension.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `24709` bytes
- Role: extension.js is JavaScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as DIRECTORY_ANALYSIS_FILENAME, LangSmith, Report, SUPPORTED_SCAN_EXTENSIONS, Snapshot for downstream use.
- Top-level symbols: `path`, `vscode`, `diagnostics_1`, `mcpClient_1`, `secrets_1`, `statusBar_1`, `documentStates`, `DIRECTORY_ANALYSIS_FILENAME`, `SUPPORTED_SCAN_EXTENSIONS`, `getConfiguration`, `isEnabled`, `getDebounceMs`
- Schema or fields: `DIRECTORY_ANALYSIS_FILENAME`, `LangSmith`, `Report`, `SUPPORTED_SCAN_EXTENSIONS`, `Snapshot`, `Status`, `Summary`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `absoluteEndLine`
- Internal references: `vscode-extension/out/diagnostics.js`, `vscode-extension/out/mcpClient.js`, `vscode-extension/out/secrets.js`, `vscode-extension/out/statusBar.js`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `vscode-extension/out/mcpClient.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `8860` bytes
- Role: mcpClient.js is JavaScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Checked, ClientCtor, EthicsMcpClient, StdioClientTransportCtor, __createBinding for downstream use.
- Top-level symbols: `path`, `fs`, `vscode`, `requireSdkStdioTransport`, `sdkPackageJson`, `loadMcpClientRuntime`, `clientModule`, `parseProgressMessage`, `parsed`, `extractStructuredContent`, `candidate`, `text`
- Schema or fields: `Checked`, `ClientCtor`, `EthicsMcpClient`, `StdioClientTransportCtor`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `activeDocumentPath`, `args`, `arguments`, `candidate`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/out/secrets.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `8623` bytes
- Role: secrets.js is JavaScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as SECRET_BY_ID, SECRET_BY_PROVIDER, SECRET_DEFINITIONS, SecretManager, __createBinding for downstream use.
- Top-level symbols: `vscode`, `SECRET_DEFINITIONS`, `SECRET_BY_ID`, `SECRET_BY_PROVIDER`, `normalizeSecret`, `trimmed`, `providerDisplayName`, `requiredSecretNameForProvider`, `SecretManager`, `overrides`, `value`, `secretName`
- Schema or fields: `SECRET_BY_ID`, `SECRET_BY_PROVIDER`, `SECRET_DEFINITIONS`, `SecretManager`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `action`, `changed`, `choice`, `definition`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/out/statusBar.js`

- Type: `source_code`
- Language: `JavaScript`
- Size: `3259` bytes
- Role: statusBar.js is JavaScript code that appears to implement application logic. It exposes 20 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Ethics, StatusBarController, __createBinding, __esModule, __importStar for downstream use.
- Top-level symbols: `vscode`, `StatusBarController`, `seconds`
- Schema or fields: `Ethics`, `StatusBarController`, `__createBinding`, `__esModule`, `__importStar`, `__setModuleDefault`, `command`, `count`, `desc`, `enumerable`, `get`, `item`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: "use strict"; var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) { if (k2 === undefined) k2 = k; var desc = Object.getOwnPropertyDescriptor(m, k); if (!desc || ("get" in de...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/src/diagnostics.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `2473` bytes
- Role: diagnostics.ts is TypeScript code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions.
- Top-level symbols: `toSeverity`, `findingToDiagnostic`, `lastLine`, `startLine`, `endLine`, `range`, `level`, `message`, `diagnostic`
- Schema or fields: `Remedy`, `Source`, `answer`, `code`, `context_quality`, `diagnostic`, `document`, `endLine`, `end_line`, `error`, `explanation`, `faithfulness`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`, `face`, `location`
- Preview note: import * as vscode from 'vscode'; export interface Finding { severity: 'HIGH' | 'MEDIUM' | 'LOW' | string; file_path: string; start_line: number; end_line: number; regulation_name: string; jurisdiction: string; explan...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/src/extension.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `24233` bytes
- Role: extension.ts is TypeScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as ActiveRun, AnalysisSnippet, DIRECTORY_ANALYSIS_FILENAME, DocumentScanState, LangSmith for downstream use.
- Top-level symbols: `documentStates`, `DIRECTORY_ANALYSIS_FILENAME`, `SUPPORTED_SCAN_EXTENSIONS`, `getConfiguration`, `isEnabled`, `getDebounceMs`, `getConfiguredProvider`, `getConfiguredModel`, `getWorkspaceTargetPath`, `activePath`, `isSupportedFilePath`, `baseName`
- Schema or fields: `ActiveRun`, `AnalysisSnippet`, `DIRECTORY_ANALYSIS_FILENAME`, `DocumentScanState`, `LangSmith`, `PendingChangeWindow`, `Report`, `SUPPORTED_SCAN_EXTENSIONS`, `Snapshot`, `Status`, `Summary`, `absoluteEndLine`
- Internal references: `vscode-extension/src/diagnostics.ts`, `vscode-extension/src/mcpClient.ts`, `vscode-extension/src/secrets.ts`, `vscode-extension/src/statusBar.ts`
- Data sources: None detected.
- Sensitive signals: `age`, `ssn`
- Preview note: import * as path from 'path'; import * as vscode from 'vscode'; import { CheckFileResult, FileResult, Finding, findingToDiagnostic } from './diagnostics'; import { DirectoryAnalysisResult, EthicsMcpClient } from './mc...
- Preview coverage: Partial preview only; larger file content was truncated for analysis.

### `vscode-extension/src/mcpClient.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `8986` bytes
- Role: mcpClient.ts is TypeScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Checked, ClientCtor, DirectoryAnalysisResult, McpClientLike, ProgressPayload for downstream use.
- Top-level symbols: `requireSdkStdioTransport`, `sdkPackageJson`, `loadMcpClientRuntime`, `clientModule`, `parseProgressMessage`, `parsed`, `extractStructuredContent`, `candidate`, `text`, `candidateSearchRoots`, `roots`, `activeDocumentPath`
- Schema or fields: `Checked`, `ClientCtor`, `DirectoryAnalysisResult`, `McpClientLike`, `ProgressPayload`, `ReviewedContextItem`, `StdioClientTransportCtor`, `StdioTransportLike`, `activeDocumentPath`, `analysis_path`, `args`, `arguments`
- Internal references: `vscode-extension/src/diagnostics.ts`
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: import * as path from 'path'; import * as fs from 'fs'; import * as vscode from 'vscode'; import type { CheckFileResult } from './diagnostics'; type ProgressPayload = { type: string; data?: unknown; }; export type Dir...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/src/secrets.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `7432` bytes
- Role: secrets.ts is TypeScript code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as ProcessEnv, SECRET_BY_ID, SECRET_BY_PROVIDER, SECRET_DEFINITIONS, SecretDefinition for downstream use.
- Top-level symbols: `SECRET_BY_ID`, `SECRET_BY_PROVIDER`, `normalizeSecret`, `trimmed`, `providerDisplayName`, `requiredSecretNameForProvider`, `SecretManager`, `value`, `secretName`, `existing`, `definition`, `action`
- Schema or fields: `ProcessEnv`, `SECRET_BY_ID`, `SECRET_BY_PROVIDER`, `SECRET_DEFINITIONS`, `SecretDefinition`, `SecretKeyName`, `action`, `boolean`, `changed`, `choice`, `definition`, `description`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: import * as vscode from 'vscode'; export type SecretKeyName = | 'GROQ_API_KEY' | 'LANGSMITH_API_KEY' | 'OLLAMA_CLOUD_API_KEY' | 'OPENROUTER_API_KEY' | 'TAVILY_API_KEY'; type SecretDefinition = { id: SecretKeyName; lab...
- Preview coverage: Full preview captured within configured limit.

### `vscode-extension/src/statusBar.ts`

- Type: `source_code`
- Language: `TypeScript`
- Size: `1714` bytes
- Role: statusBar.ts is TypeScript code that appears to implement application logic. It exposes 8 recognizable fields and 0 data sources. This summary is structural context for the LLM review, not the final compliance judgement.
- Objective/output: This file transforms records with fields such as Ethics, command, count, delayMs, item for downstream use.
- Top-level symbols: `StatusBarController`, `seconds`
- Schema or fields: `Ethics`, `command`, `count`, `delayMs`, `item`, `seconds`, `text`, `tooltip`
- Internal references: None resolved.
- Data sources: None detected.
- Sensitive signals: `age`
- Preview note: import * as vscode from 'vscode'; export class StatusBarController implements vscode.Disposable { private readonly item: vscode.StatusBarItem; constructor() { this.item = vscode.window.createStatusBarItem(vscode.Statu...
- Preview coverage: Full preview captured within configured limit.
