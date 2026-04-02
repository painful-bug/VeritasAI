from __future__ import annotations

from prompts.loader import load_prompt
from tools.filesystem_tools import read_file_tool, run_bash_tool
from tools.rag_tool import query_rag_tool
from tools.web_search_tool import web_search_tool



def build_data_validator_agent(llm):
    try:
        from langchain_core.messages import SystemMessage
        from langgraph.prebuilt import create_react_agent
    except Exception:
        return None

    tools = [read_file_tool, run_bash_tool, query_rag_tool, web_search_tool]
    system_prompt = load_prompt("data_source_validator")
    message = SystemMessage(content=system_prompt)
    try:
        return create_react_agent(model=llm, tools=tools, prompt=message)
    except TypeError:
        try:
            return create_react_agent(model=llm, tools=tools, state_modifier=message)
        except Exception:
            return None
