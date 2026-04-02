from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from graphs.checkpointer import get_checkpointer
from models.state import ComplianceState
from nodes.initialize import initialize_node
from nodes.review_file import review_file_node
from nodes.write_report import write_report_node


def build_compliance_graph() -> StateGraph:
    builder = StateGraph(ComplianceState)
    builder.add_node("initialize", initialize_node)
    builder.add_node("review_file", review_file_node)
    builder.add_node("write_report", write_report_node)
    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "review_file")
    builder.add_edge("review_file", "write_report")
    builder.add_edge("write_report", END)
    return builder


def compile_graph(checkpointer=None, config: dict | None = None):
    builder = build_compliance_graph()
    active_checkpointer = get_checkpointer(config) if checkpointer is None else checkpointer
    return builder.compile(checkpointer=active_checkpointer)
