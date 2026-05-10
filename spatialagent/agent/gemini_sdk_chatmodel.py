"""LangChain ChatModel wrapping the google-genai SDK with tool calling support.

GeminiSDKChatModel: wraps google.genai for full agentic tool calling.
"""

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Type, Union

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_GEMINI_SDK_MODEL = "gemini-3-flash-preview"

# Map short names used in make_llm to full model resource names.
MODEL_RESOURCE_MAP: Dict[str, str] = {
    "gemini-2.5-pro": "models/gemini-2.5-pro",
    "gemini-2.5-flash": "models/gemini-2.5-flash",
    "gemini-2.0-flash": "models/gemini-2.0-flash",
    "gemini-3-pro-preview": "models/gemini-3-pro-preview",
    "gemini-3-flash-preview": "models/gemini-3-flash-preview",
    "gemini-3.1-pro-preview": "models/gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite": "models/gemini-3.1-flash-lite",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api_key() -> str:
    """Resolve Gemini API key from environment or ~/.gemini/.env file."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if key:
        return key
    # Fallback: read from ~/.gemini/.env
    try:
        dotenv_path = os.path.expanduser("~/.gemini/.env")
        with open(dotenv_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except (FileNotFoundError, IOError, OSError):
        pass
    return ""


def _resolve_model_resource(model: str) -> str:
    """Map short model name to full resource path for the API."""
    if model.startswith("models/"):
        return model
    return MODEL_RESOURCE_MAP.get(model, f"models/{model}")


def _to_gemini_content(
    messages: List[BaseMessage],
) -> tuple[Optional[str], List[Dict[str, Any]]]:
    """Convert LangChain messages to Gemini content format.

    Returns:
        (system_instruction_text, contents_list)
    """
    system_text: Optional[str] = None
    contents: List[Dict[str, Any]] = []

    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Gemini uses system_instruction at the top level
            system_text = _extract_text(msg.content)
            continue

        role = _gemini_role(msg)
        parts: List[Dict[str, Any]] = []

        if isinstance(msg, AIMessage) and msg.tool_calls:
            # Tool call requests from the assistant
            for tc in msg.tool_calls:
                try:
                    args = (
                        json.loads(tc["args"])
                        if isinstance(tc["args"], str)
                        else tc["args"]
                    )
                except (json.JSONDecodeError, TypeError):
                    args = {}
                parts.append({
                    "function_call": {
                        "name": tc["name"],
                        "args": args,
                    }
                })
        elif isinstance(msg, (ToolMessage, FunctionMessage)):
            parts.append({
                "function_response": {
                    "name": msg.name or "unknown_function",
                    "response": {"result": _extract_text(msg.content)},
                }
            })
        else:
            text = _extract_text(msg.content)
            if text:
                parts.append({"text": text})

        if parts:
            contents.append({"role": role, "parts": parts})

    return system_text, contents


def _extract_text(content: Any) -> str:
    """Extract plain text from various LangChain message content formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                item_text = item.get("text") or item.get("content") or ""
                if isinstance(item_text, str):
                    texts.append(item_text)
        return " ".join(texts)
    return str(content) if content else ""


def _gemini_role(message: BaseMessage) -> str:
    """Map LangChain message types to Gemini roles."""
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "model"
    if isinstance(message, ToolMessage):
        return "function"
    if isinstance(message, FunctionMessage):
        return "function"
    return "user"


def _convert_tools_to_gemini(
    tools: Optional[List[Any]],
) -> Optional[List[Dict[str, Any]]]:
    """Convert LangChain tool definitions to Gemini FunctionDeclaration format.

    Handles:
      - Pydantic BaseModel (schema-only tools)
      - LangChain BaseTool instances
      - Raw dict tool definitions
    """
    if not tools:
        return None

    declarations = []
    for tool in tools:
        fd = _tool_to_function_declaration(tool)
        if fd:
            declarations.append(fd)

    if not declarations:
        return None

    return [{"function_declarations": declarations}]


def _tool_to_function_declaration(
    tool: Any,
) -> Optional[Dict[str, Any]]:
    """Convert a single tool definition to Gemini FunctionDeclaration."""
    # Case 1: Pydantic BaseModel (schema-only tool)
    if isinstance(tool, type) and issubclass(tool, BaseModel):
        schema = _base_model_to_json_schema(tool)
        return {
            "name": tool.__name__,
            "description": tool.__doc__ or "",
            "parameters": schema,
        }

    # Case 2: LangChain BaseTool
    if isinstance(tool, BaseTool):
        params = {}
        if tool.args_schema:
            params = _base_model_to_json_schema(tool.args_schema)
        elif tool.args:
            # Flat dict schema
            properties = {}
            for arg_name, arg_info in tool.args.items():
                properties[arg_name] = {
                    "type": arg_info.get("type", "string"),
                    "description": arg_info.get("description", ""),
                }
            required = [
                k
                for k, v in tool.args.items()
                if v.get("required", False)
            ]
            params = {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        return {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": params,
        }

    # Case 3: Raw dict with name/description/parameters
    if isinstance(tool, dict):
        name = tool.get("name", "unknown")
        description = tool.get("description", "")
        parameters = tool.get("parameters", tool.get("input_schema", {}))
        return {
            "name": name,
            "description": description,
            "parameters": parameters,
        }

    return None


def _base_model_to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic BaseModel to JSON schema (OpenAPI-compatible)."""
    schema = model.model_json_schema()
    # Gemini expects 'type' at root
    if "type" not in schema:
        schema["type"] = "object"
    return schema


def _parse_gemini_response(
    response: Any,
    stop: Optional[List[str]] = None,
) -> AIMessage:
    """Parse a google.genai GenerateContentResponse into an AIMessage."""
    if not response.candidates:
        return AIMessage(
            content="",
            additional_kwargs={"finish_reason": "UNKNOWN"},
        )

    candidate = response.candidates[0]
    finish_reason = str(candidate.finish_reason or "UNKNOWN")
    content_parts = candidate.content.parts if candidate.content else []

    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []

    for part in content_parts:
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

        if hasattr(part, "function_call") and part.function_call:
            fc = part.function_call
            tool_call_id = f"call_{fc.name}"
            try:
                args = (
                    {k: v for k, v in fc.args.items()}
                    if hasattr(fc.args, "items")
                    else fc.args
                )
            except Exception:
                args = {}
            tool_calls.append({
                "name": fc.name,
                "args": args,
                "id": tool_call_id,
                "type": "tool_call",
            })

    text = "".join(text_parts)

    # Apply stop sequences client-side
    if stop:
        earliest = min(
            (text.find(seq) for seq in stop if seq and seq in text),
            default=-1,
        )
        if earliest >= 0:
            text = text[:earliest]

    additional_kwargs = {
        "finish_reason": finish_reason,
        "candidate": str(candidate),
    }

    kwargs: Dict[str, Any] = {
        "content": text,
        "additional_kwargs": additional_kwargs,
    }
    if tool_calls:
        kwargs["tool_calls"] = tool_calls

    return AIMessage(**kwargs)


# ---------------------------------------------------------------------------
# SDK ChatModel
# ---------------------------------------------------------------------------


class GeminiSDKChatModel(BaseChatModel):
    """LangChain ChatModel wrapping google.genai SDK with agentic tool calling.

    Uses GEMINI_API_KEY env var by default. Supports bind_tools() for
    full function-calling integration with LangGraph agents.

    Example::

        llm = GeminiSDKChatModel(model="gemini-2.5-pro")
        llm_with_tools = llm.bind_tools([my_tool_schema])

        result = llm_with_tools.invoke("analyze this tissue sample")
        # result.tool_calls -> parsed function calls
    """

    model: str = DEFAULT_GEMINI_SDK_MODEL
    api_key: Optional[str] = None
    timeout: int = 120

    # Internal: stores tools bound via bind_tools()
    _tools: Optional[List[Any]] = None

    model_config = {"protected_namespaces": ()}

    @property
    def _llm_type(self) -> str:
        return "gemini-sdk"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "timeout": self.timeout,
            "has_tools": self._tools is not None,
        }

    def bind_tools(
        self,
        tools: Sequence[Union[Type[BaseModel], BaseTool, Dict[str, Any]]],
        *,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> "GeminiSDKChatModel":
        """Bind tools for agentic function calling.

        Accepts Pydantic BaseModel schemas, LangChain BaseTool instances,
        or raw dict tool definitions.
        """
        copied = self.model_copy()
        copied._tools = list(tools)
        return copied

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_text, contents = _to_gemini_content(messages)

        # Build the Gemini tool config
        gemini_tools = _convert_tools_to_gemini(self._tools)

        # Deferred import so the SDK is only required at runtime
        try:
            from google.genai import Client, types
        except ImportError:
            return _error_chat_result(
                "google-genai SDK not installed. Run: pip install google-genai",
                stop,
            )

        api_key = self.api_key or _api_key()
        if not api_key:
            return _error_chat_result(
                "Gemini API key not found. Set GEMINI_API_KEY env var.",
                stop,
            )

        # Save and clear GOOGLE_GEMINI_BASE_URL (Gemini CLI setting) to prevent
        # it from interfering with the google-genai SDK's endpoint resolution.
        _saved_base_url = os.environ.pop("GOOGLE_GEMINI_BASE_URL", None)

        client = Client(api_key=api_key)
        resource_name = _resolve_model_resource(self.model)

        # Build generation config
        gen_config = {}
        if stop:
            gen_config["stop_sequences"] = list(stop)

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_text,
                tools=gemini_tools,
                **gen_config,
                **kwargs,
            )

            response = client.models.generate_content(
                model=resource_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            return _error_chat_result(
                f"Gemini SDK error: {_redact_credentials(str(exc))}",
                stop,
            )
        finally:
            # Restore GOOGLE_GEMINI_BASE_URL if we cleared it
            if _saved_base_url is not None:
                os.environ["GOOGLE_GEMINI_BASE_URL"] = _saved_base_url

        message = _parse_gemini_response(response, stop)
        return ChatResult(
            generations=[ChatGeneration(message=message)],
            llm_output={
                "model": self.model,
                "token_usage": _extract_usage(response),
            },
        )


# ---------------------------------------------------------------------------
# Internal helpers (continued)
# ---------------------------------------------------------------------------


def _error_chat_result(
    error_text: str,
    stop: Optional[List[str]] = None,
) -> ChatResult:
    """Build a ChatResult wrapping an error message."""
    if stop:
        earliest = min(
            (error_text.find(seq) for seq in stop if seq and seq in error_text),
            default=-1,
        )
        if earliest >= 0:
            error_text = error_text[:earliest]
    return ChatResult(
        generations=[ChatGeneration(message=AIMessage(content=error_text))]
    )


def _extract_usage(response: Any) -> Dict[str, int]:
    """Extract token usage from a Gemini response."""
    if not hasattr(response, "usage_metadata") or not response.usage_metadata:
        return {}
    um = response.usage_metadata
    return {
        "prompt_tokens": getattr(um, "prompt_token_count", 0) or 0,
        "completion_tokens": getattr(um, "candidates_token_count", 0) or 0,
        "total_tokens": getattr(um, "total_token_count", 0) or 0,
    }


def _redact_credentials(text: str) -> str:
    """Remove API keys and tokens from error messages."""
    import re

    patterns = [
        re.compile(r"(?i)(api[_-]?key[\s\"']*[:=][\s\"']*)([^\s,;\"']+)"),
        re.compile(r"(?i)(key[\s\"']*[:=][\s\"']*)([A-Za-z0-9_-]{10,})"),
    ]
    for pattern in patterns:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text
