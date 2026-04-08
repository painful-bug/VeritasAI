<!-- DIRECTORY_ANALYSIS_META {"version": 1, "generated_at": "2026-04-08T11:06:11.637625+00:00", "workspace_root": "/Users/aishik/Documents/Programming/ethics_agent", "snapshot_hash": "e03c664c7db2ed4ac6bed859964af2bb7a2db707a7c53169cbe1e3719b55739e", "file_count": 97, "directory_count": 34} -->

# Directory Analysis

Generated: `2026-04-08T11:06:11.637625+00:00`
Workspace root: `/Users/aishik/Documents/Programming/ethics_agent`
Snapshot hash: `e03c664c7db2ed4ac6bed859964af2bb7a2db707a7c53169cbe1e3719b55739e`
Files analysed: `97`
Directories analysed: `34`

## Repository Overview

- Purpose: The project is now a VS Code-first AI ethics reviewer. A TypeScript extension watches the active editor, waits 5 seconds after the last change, and calls a Python LangGraph backend over MCP stdio. Findings are surface...
- Main themes: fields, that, implement, exposes, recognizable, sources
- Dominant languages: Python (61), JavaScript (6), TypeScript (5), Shell (1)
- File type mix: source_code (73), document (14), structured_data (10)
- Likely entrypoints: `mcp_server.py`, `analysis/repository_review.py`, `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`, `demo_violations/india_eu_unethical_suite/src/no_oversight_or_redress.py`, `demo_violations/india_eu_unethical_suite/src/run_all.py`, `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py`

## Directory Map

- `.`: Workspace root containing top-level project assets. Files=`5`. Languages=Python (2). Children=`README.md`, `analysis`, `config.yaml`, `config_loader.py`, `demo_violations`, `docs`, `graphs`, `knowledge`. Key files=`README.md`, `config.yaml`, `config_loader.py`, `mcp_server.py`
- `.streamlit`: .streamlit primarily contains mixed content. Files=`0`. Languages=None. Children=None. Key files=None
- `.tmp_chroma_test`: .tmp_chroma_test primarily contains mixed content. Files=`0`. Languages=None. Children=None. Key files=None
- `.tmp_chroma_test2`: .tmp_chroma_test2 primarily contains mixed content. Files=`0`. Languages=None. Children=None. Key files=None
- `analysis`: Core analysis and detection logic. Files=`6`. Languages=Python (6). Children=`__init__.py`, `agentic_runtime.py`, `core.py`, `llm_review.py`, `reports.py`, `repository_review.py`. Key files=`analysis/agentic_runtime.py`, `analysis/core.py`, `analysis/reports.py`, `analysis/repository_review.py`
- `demo_violations`: Example fixtures and intentionally unsafe scenarios used to exercise detections. Files=`0`. Languages=None. Children=`india_eu_directive_breach`, `india_eu_unethical_suite`, `unsafe_hiring_fixture`. Key files=None
- `demo_violations/global_ai_acts_violation_suite`: global_ai_acts_violation_suite primarily contains mixed content. Files=`0`. Languages=None. Children=None. Key files=None
- `demo_violations/global_ai_acts_violation_suite/src`: src primarily contains mixed content. Files=`0`. Languages=None. Children=None. Key files=None
- `demo_violations/india_eu_directive_breach`: india_eu_directive_breach primarily contains source code. Files=`1`. Languages=Python (1). Children=`__init__.py`. Key files=`demo_violations/india_eu_directive_breach/__init__.py`
- `demo_violations/india_eu_directive_breach/data`: Input datasets or tabular records consumed by the project. Files=`0`. Languages=None. Children=None. Key files=None
- `demo_violations/india_eu_unethical_suite`: india_eu_unethical_suite primarily contains document. Files=`1`. Languages=None. Children=`README.md`, `config`, `data`, `docs`, `src`. Key files=`demo_violations/india_eu_unethical_suite/README.md`
- `demo_violations/india_eu_unethical_suite/config`: Configuration artifacts that tune runtime behavior. Files=`1`. Languages=None. Children=`policy_bypass.yaml`. Key files=`demo_violations/india_eu_unethical_suite/config/policy_bypass.yaml`
- `demo_violations/india_eu_unethical_suite/data`: Input datasets or tabular records consumed by the project. Files=`4`. Languages=None. Children=`candidates_sensitive.csv`, `citizen_scoring.csv`, `release_plan.csv`, `surveillance_feed.csv`. Key files=`demo_violations/india_eu_unethical_suite/data/candidates_sensitive.csv`, `demo_violations/india_eu_unethical_suite/data/citizen_scoring.csv`, `demo_violations/india_eu_unethical_suite/data/release_plan.csv`, `demo_violations/india_eu_unethical_suite/data/surveillance_feed.csv`
- `demo_violations/india_eu_unethical_suite/docs`: Supporting documentation and narrative context. Files=`1`. Languages=None. Children=`violations_map.md`. Key files=`demo_violations/india_eu_unethical_suite/docs/violations_map.md`
- `demo_violations/india_eu_unethical_suite/src`: src primarily contains source code. Files=`8`. Languages=Python (8). Children=`__init__.py`, `biometric_surveillance.py`, `deepfake_campaign.py`, `hiring_bias_engine.py`, `no_oversight_or_redress.py`, `run_all.py`, `settings.py`, `social_scoring_system.py`. Key files=`demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`, `demo_violations/india_eu_unethical_suite/src/run_all.py`, `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py`
- `demo_violations/unsafe_hiring_fixture`: unsafe_hiring_fixture primarily contains document. Files=`2`. Languages=Python (1). Children=`README.md`, `data`, `unsafe_hiring_screen.py`. Key files=`demo_violations/unsafe_hiring_fixture/README.md`, `demo_violations/unsafe_hiring_fixture/unsafe_hiring_screen.py`
- `demo_violations/unsafe_hiring_fixture/data`: Input datasets or tabular records consumed by the project. Files=`1`. Languages=None. Children=`applicants_sensitive.csv`. Key files=`demo_violations/unsafe_hiring_fixture/data/applicants_sensitive.csv`
- `docs`: Supporting documentation and narrative context. Files=`5`. Languages=None. Children=`AGENTS.md`, `ARCHITECTURE.md`, `EXTENSION_PUBLISH.md`, `PRD_ui.md`, `PRD_vscode_extension.md`. Key files=`docs/AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/EXTENSION_PUBLISH.md`, `docs/PRD_ui.md`
- `graphs`: Workflow orchestration and graph composition. Files=`4`. Languages=Python (4). Children=`__init__.py`, `checkpointer.py`, `compliance_graph.py`, `file_review_subgraph.py`. Key files=`graphs/__init__.py`, `graphs/checkpointer.py`, `graphs/compliance_graph.py`, `graphs/file_review_subgraph.py`
- `knowledge`: Knowledge-base assets used for retrieval. Files=`1`. Languages=None. Children=`ai_ethics_knowledge_base.pdf`. Key files=`knowledge/ai_ethics_knowledge_base.pdf`
- `llm`: Model-provider setup and LLM-facing adapters. Files=`2`. Languages=Python (2). Children=`__init__.py`, `provider_factory.py`. Key files=`llm/__init__.py`, `llm/provider_factory.py`
- `models`: Shared typed models and state definitions. Files=`3`. Languages=Python (3). Children=`__init__.py`, `events.py`, `state.py`. Key files=`models/__init__.py`, `models/events.py`, `models/state.py`
- `nodes`: Graph node implementations and execution steps. Files=`5`. Languages=Python (5). Children=`__init__.py`, `initialize.py`, `review_file.py`, `review_repository.py`, `write_report.py`. Key files=`nodes/initialize.py`, `nodes/review_file.py`, `nodes/review_repository.py`, `nodes/write_report.py`
- `prompts`: Prompt assets consumed by the agentic runtime. Files=`2`. Languages=Python (1). Children=`file_reviewer.md`, `loader.py`. Key files=`prompts/file_reviewer.md`, `prompts/loader.py`

- Additional directories omitted from the summary: `10`

## Cross-file Relationships

- `analysis/agentic_runtime.py` -> `prompts/loader.py`, `rag/retriever.py`, `utils/strings.py`
- `analysis/core.py` -> `config_loader.py`, `models/state.py`, `tools/filesystem_tools.py`
- `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py` -> `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py` -> `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py` -> `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/run_all.py` -> `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`
- `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py` -> `demo_violations/india_eu_unethical_suite/src/settings.py`
- `graphs/file_review_subgraph.py` -> `prompts/loader.py`, `tools/filesystem_tools.py`, `tools/rag_tool.py`
- `mcp_server.py` -> `config_loader.py`, `analysis/repository_review.py`, `graphs/compliance_graph.py`
- `nodes/initialize.py` -> `models/events.py`, `models/state.py`, `tools/filesystem_tools.py`
- `nodes/review_file.py` -> `analysis/core.py`, `analysis/llm_review.py`, `llm/provider_factory.py`
- `nodes/review_repository.py` -> `analysis/repository_review.py`, `models/events.py`, `models/state.py`

## Key Files

- `analysis/agentic_runtime.py`: agentic_runtime.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data... | refs: `prompts/loader.py`, `rag/retriever.py`, `utils/strings.py`
- `analysis/core.py`: core.py is Python code that appears to implement model training, automated scoring or inference, data collection. It exposes 30 recogniza... | refs: `config_loader.py`, `models/state.py`, `tools/filesystem_tools.py`
- `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`: biometric_surveillance.py is Python code that appears to implement automated scoring or inference. It exposes 8 recognizable fields and 0... | entrypoint | refs: `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`: hiring_bias_engine.py is Python code that appears to implement automated scoring or inference. It exposes 14 recognizable fields and 0 da... | entrypoint | refs: `demo_violations/india_eu_unethical_suite/src/settings.py`
- `demo_violations/india_eu_unethical_suite/src/run_all.py`: run_all.py is Python code that appears to implement application logic. It exposes 7 recognizable fields and 0 data sources. This summary... | entrypoint | refs: `demo_violations/india_eu_unethical_suite/src/biometric_surveillance.py`, `demo_violations/india_eu_unethical_suite/src/deepfake_campaign.py`, `demo_violations/india_eu_unethical_suite/src/hiring_bias_engine.py`
- `demo_violations/india_eu_unethical_suite/src/social_scoring_system.py`: social_scoring_system.py is Python code that appears to implement automated scoring or inference. It exposes 11 recognizable fields and 0... | entrypoint | refs: `demo_violations/india_eu_unethical_suite/src/settings.py`
- `mcp_server.py`: mcp_server.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summ... | entrypoint | refs: `config_loader.py`, `analysis/repository_review.py`, `graphs/compliance_graph.py`
- `nodes/initialize.py`: initialize.py is Python code that appears to implement application logic. It exposes 8 recognizable fields and 0 data sources. This summa... | refs: `models/events.py`, `models/state.py`, `tools/filesystem_tools.py`
- `nodes/review_file.py`: review_file.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data sour... | refs: `analysis/core.py`, `analysis/llm_review.py`, `llm/provider_factory.py`
- `nodes/review_repository.py`: review_repository.py is Python code that appears to implement application logic. It exposes 22 recognizable fields and 0 data sources. Th... | refs: `analysis/repository_review.py`, `models/events.py`, `models/state.py`
- `nodes/write_report.py`: write_report.py is Python code that appears to implement application logic. It exposes 18 recognizable fields and 0 data sources. This su... | refs: `analysis/core.py`, `analysis/reports.py`, `models/events.py`
- `rag/ingestor.py`: ingestor.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. This summar... | refs: `config_loader.py`, `rag/storage.py`, `utils/compat.py`
- `rag/retriever.py`: retriever.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0 data source... | refs: `config_loader.py`, `rag/storage.py`, `utils/compat.py`
- `scripts/ingest_knowledge_base.py`: ingest_knowledge_base.py is Python code that appears to implement automated scoring or inference. It exposes 30 recognizable fields and 0... | entrypoint | refs: `config_loader.py`, `rag/ingestor.py`, `rag/retriever.py`
- `scripts/verify_demo_scan.py`: verify_demo_scan.py is Python code that appears to implement application logic. It exposes 30 recognizable fields and 0 data sources. Thi... | entrypoint | refs: `config_loader.py`, `graphs/compliance_graph.py`, `rag/ingestor.py`
- `tests/test_llm_review.py`: test_llm_review.py is Python code that appears to implement model training, automated scoring or inference. It exposes 28 recognizable fi... | refs: `analysis/llm_review.py`
- `tests/test_mcp_server.py`: test_mcp_server.py is Python code that appears to implement model training, automated scoring or inference. It exposes 16 recognizable fi... | refs: `mcp_server.py`, `nodes/review_file.py`, `graphs/compliance_graph.py`
- `tools/rag_tool.py`: rag_tool.py is Python code that appears to implement application logic. It exposes 12 recognizable fields and 0 data sources. This summar... | refs: `config_loader.py`, `rag/retriever.py`, `utils/compat.py`

- Additional files omitted from the summary: `79`
