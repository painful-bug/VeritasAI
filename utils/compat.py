from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _passthrough_decorator(func: F) -> F:
    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any):
        return func(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def tool(*args: Any, **kwargs: Any):
    """Compatibility-safe tool decorator that keeps functions directly callable."""
    del kwargs
    if args and callable(args[0]) and len(args) == 1:
        return args[0]

    def decorator(func: F) -> F:
        return func

    return decorator


def traceable(*args: Any, **kwargs: Any):
    """Fallback-safe LangSmith @traceable decorator."""
    try:
        from langsmith import traceable as langsmith_traceable

        return langsmith_traceable(*args, **kwargs)
    except Exception:
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return _passthrough_decorator(args[0])

        def decorator(func: F) -> F:
            return _passthrough_decorator(func)

        return decorator


def get_runnable_config_type():
    try:
        from langchain_core.runnables import RunnableConfig

        return RunnableConfig
    except Exception:
        return dict


def get_tool_exception_type():
    try:
        from langchain_core.tools import ToolException

        return ToolException
    except Exception:
        return RuntimeError
