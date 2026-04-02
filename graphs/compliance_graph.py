from __future__ import annotations

from models.state import ComplianceState
from nodes.fan_out import fan_out_files_node
from nodes.initialize import initialize_node
from nodes.join_results import join_results_node
from nodes.review_file import review_file_node
from nodes.validate_data_source import validate_data_source_node
from nodes.write_reports import write_reports_node



def should_validate_data_source(state: ComplianceState):
    pending = state.get("_pending_data_sources", [])
    return "validate_data_source" if pending else "join_results"



def fan_out_routes(state: ComplianceState):
    all_files = state.get("all_files", [])
    if not all_files:
        return "join_results"

    from langgraph.constants import Send

    return [
        Send(
            "review_file",
            {
                **state,
                "_current_file": file_path,
                "_current_category": state.get("file_categories", {}).get(file_path, "binary_unknown"),
            },
        )
        for file_path in all_files
    ]



def build_compliance_graph():
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(ComplianceState)
    builder.add_node("initialize", initialize_node)
    builder.add_node("fan_out_files", fan_out_files_node)
    builder.add_node("review_file", review_file_node)
    builder.add_node("validate_data_source", validate_data_source_node)
    builder.add_node("join_results", join_results_node)
    builder.add_node("write_reports", write_reports_node)

    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "fan_out_files")
    builder.add_conditional_edges("fan_out_files", fan_out_routes, {"join_results": "join_results"})
    builder.add_conditional_edges(
        "review_file",
        should_validate_data_source,
        {"validate_data_source": "validate_data_source", "join_results": "join_results"},
    )
    builder.add_edge("validate_data_source", "join_results")
    builder.add_edge("join_results", "write_reports")
    builder.add_edge("write_reports", END)
    return builder



def compile_graph(checkpointer=None, config: dict | None = None):
    from graphs.checkpointer import get_checkpointer

    builder = build_compliance_graph()
    active_checkpointer = checkpointer or get_checkpointer(config)
    return builder.compile(checkpointer=active_checkpointer)
