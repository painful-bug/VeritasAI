from __future__ import annotations

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from prompts.loader import load_prompt
from tools.filesystem_tools import read_file_tool, write_file_tool
from tools.rag_tool import query_rag_tool


def build_file_review_agent(llm):
    tools = [read_file_tool, write_file_tool, query_rag_tool]
    prompt = SystemMessage(content=load_prompt("file_reviewer"))
    return create_react_agent(model=llm, tools=tools, prompt=prompt)
