#!/usr/bin/env python3

"""
Minimal MCP HITL server

Exposes a single tool `ask_clarification` that elicits structured user input
via MCP elicitation (rendered by clients like Cursor, VS Code, Claude Desktop).

Run locally (stdio transport):
  uv venv && uv pip install fastmcp
  python hitl_server.py

Then register this server in your MCP-enabled client configuration
as a stdio server that runs `python hitl_server.py`.

For full documentation, see README.md
"""

from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass
try:
    from pydantic import BaseModel  # Prefer Pydantic v2 if available
    import pydantic as _p
    _PYDANTIC_MAJOR = int(getattr(_p, 'VERSION', '2').split('.')[0])
except Exception as e:
    # Fall back to a minimal shim if Pydantic is unavailable; we'll use JSON schema instead
    BaseModel = object  # type: ignore
    _PYDANTIC_MAJOR = 0
import inspect

try:
    from mcp.server.fastmcp import FastMCP, Context
    from mcp.server.session import ServerSession
except Exception as e:  # ImportError or SDK not installed
    raise SystemExit(
        "MCP Python SDK not installed. Install with:\n"
        "  uv venv && uv pip install fastmcp\n"
        f"Import error: {e}"
    )

# Optional: Import error handling middleware if available
try:
    from mcp.server.fastmcp.middleware import ErrorHandlingMiddleware
    _HAS_ERROR_MIDDLEWARE = True
except ImportError:
    _HAS_ERROR_MIDDLEWARE = False


mcp = FastMCP("mcp-clarify")

# Add error handling middleware if available
if _HAS_ERROR_MIDDLEWARE:
    mcp.add_middleware(ErrorHandlingMiddleware(
        include_traceback=True,
        transform_errors=True
    ))


class ClarifyAnswer(BaseModel):
    """Pydantic model used to render a simple one-field form in MCP clients."""
    answer: str  # Short answer (<= 5 words)

# Provide a v1-to-v2 compatibility shim if running on Pydantic v1
try:
    if _PYDANTIC_MAJOR and _PYDANTIC_MAJOR < 2:  # pragma: no cover
        # Map v2-style attribute expected by some FastMCP builds
        setattr(ClarifyAnswer, 'model_fields', getattr(ClarifyAnswer, '__fields__', {}))  # type: ignore[attr-defined]
except Exception:
    pass


@mcp.tool()
async def ask_clarification(ctx: Context[ServerSession, None], prompt: str, choices: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Ask a single clarification question and capture a concise answer.

    Uses FastMCP elicitation with a Pydantic schema so that MCP clients 
    (Cursor, VS Code, Claude Desktop) render a small input form.

    Args:
        prompt: The human-visible question to ask (e.g., "Pick target latency SLA?")
        choices: Optional list of suggested answers. When provided, clients that
            honor JSON Schema enums will render these as selectable options.

    Returns:
        JSON with fields: {"question": str, "answer": str}
    """
    import asyncio
    
    # Show choices on separate lines for readability
    display_prompt = prompt
    if choices:
        lines = "\n".join(f"{i+1}) {str(c)}" for i, c in enumerate(choices))
        display_prompt = f"{prompt}\n\nOptions:\n{lines}\n(Type the value or its number)"
    
    # MCP elicitation only supports primitive types (str, int, float, bool)
    # Use the simple ClarifyAnswer model with string field for all cases
    # Choices are displayed in the prompt text and handled in post-processing
    schema_model = ClarifyAnswer
    
    # Use a single elicitation call with proper timeout (60 seconds)
    # This prevents duplicate responses and race conditions
    try:
        result = await asyncio.wait_for(
            ctx.elicit(message=display_prompt, schema=schema_model),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        raise TimeoutError("MCP error -32001: Clarification request timed out after 60 seconds")
    except Exception as e:
        # Catch and re-raise as a clear error
        raise RuntimeError(f"Elicitation failed: {str(e)}") from e

    answer = ""
    # FastMCP returns an object with fields like action (accept/decline/cancel) and data
    action = getattr(result, "action", None)
    data = getattr(result, "data", None)
    
    if action == "accept" and data is not None:
        try:
            # Handle dataclass-like, dict, or simple types
            if hasattr(data, "answer"):
                answer = str(getattr(data, "answer")).strip()
            elif isinstance(data, dict):
                answer = str(data.get("answer", "")).strip() or str(data).strip()
            else:
                answer = str(data).strip()
        except Exception:
            answer = str(data).strip()
    else:
        # If no action/data contract, attempt direct extraction
        try:
            if hasattr(result, "answer"):
                answer = str(getattr(result, "answer")).strip()
            elif isinstance(result, dict) and "answer" in result:
                answer = str(result["answer"]).strip()
            else:
                # Treat entire result as the answer text
                answer = str(result).strip()
        except Exception:
            answer = ""

    # If choices were provided, coerce numeric selection or case-insensitive match
    if choices and isinstance(answer, str):
        raw = answer.strip()
        selected = None
        # Accept formats like "1", "1)", "1.", "1: dev"
        try:
            token = raw.split()[0].rstrip(").:]")
            if token.isdigit():
                idx = int(token)
                if 1 <= idx <= len(choices):
                    selected = str(choices[idx - 1])
        except Exception:
            pass
        if selected is None:
            for c in choices:
                if raw.lower() == str(c).lower():
                    selected = str(c)
                    break
        # Only override when we identified a valid selection
        if selected is not None:
            answer = selected

    return {"question": prompt, "answer": answer}


if __name__ == "__main__":
    mcp.run(transport="stdio")


