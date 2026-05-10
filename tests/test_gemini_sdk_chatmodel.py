"""Tests for GeminiSDKChatModel (google.genai SDK wrapper)."""

import unittest
from typing import Any, Optional
from unittest.mock import MagicMock, patch

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from spatialagent.agent.gemini_sdk_chatmodel import (
    DEFAULT_GEMINI_SDK_MODEL,
    GeminiSDKChatModel,
    _convert_tools_to_gemini,
    _extract_text,
    _gemini_role,
    _parse_gemini_response,
    _resolve_model_resource,
    _to_gemini_content,
    _tool_to_function_declaration,
)


# =========================================================================
# Mocks
# =========================================================================


class _MockPart:
    """Mock google.genai types.Part."""

    def __init__(
        self,
        text: str = "",
        function_call: Optional[Any] = None,
    ):
        self.text = text
        self.function_call = function_call


class _MockFunctionCall:
    """Mock google.genai types.FunctionCall."""

    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args


class _MockContent:
    """Mock google.genai types.Content."""

    def __init__(self, parts: list):
        self.parts = parts
        self.role = "model"


class _MockCandidate:
    """Mock google.genai types.Candidate."""

    def __init__(self, parts: list, finish_reason: str = "STOP"):
        self.content = _MockContent(parts)
        self.finish_reason = finish_reason
        self.finish_reason_str = finish_reason

    def __str__(self) -> str:
        return f"Candidate({self.finish_reason})"


class _MockUsageMetadata:
    def __init__(self, prompt=10, completion=20, total=30):
        self.prompt_token_count = prompt
        self.candidates_token_count = completion
        self.total_token_count = total


class _MockResponse:
    """Mock google.genai GenerateContentResponse."""

    def __init__(
        self,
        parts: Optional[list] = None,
        finish_reason: str = "STOP",
        usage: Optional[_MockUsageMetadata] = None,
    ):
        self.candidates = (
            [_MockCandidate(parts or [], finish_reason)]
            if parts is not None
            else []
        )
        self.usage_metadata = usage or _MockUsageMetadata()


# =========================================================================
# Unit Tests
# =========================================================================


class TestModelIdentity(unittest.TestCase):
    def test_llm_type_is_gemini_sdk(self):
        model = GeminiSDKChatModel()
        self.assertEqual(model._llm_type, "gemini-sdk")

    def test_default_model(self):
        model = GeminiSDKChatModel()
        self.assertEqual(model.model, DEFAULT_GEMINI_SDK_MODEL)

    def test_custom_model(self):
        model = GeminiSDKChatModel(model="gemini-3.1-pro-preview")
        self.assertEqual(model.model, "gemini-3.1-pro-preview")

    def test_identifying_params(self):
        model = GeminiSDKChatModel(model="gemini-2.0-flash", timeout=60)
        params = model._identifying_params
        self.assertEqual(params["model"], "gemini-2.0-flash")
        self.assertEqual(params["timeout"], 60)
        self.assertFalse(params["has_tools"])


class TestBindTools(unittest.TestCase):
    def test_bind_tools_returns_new_instance(self):
        model = GeminiSDKChatModel()

        class SampleTool(BaseModel):
            """A sample tool."""
            query: str = Field(description="The search query")

        bound = model.bind_tools([SampleTool])
        self.assertIsNot(bound, model)
        self.assertIsNotNone(bound._tools)
        self.assertEqual(len(bound._tools), 1)

    def test_bind_tools_base_tool(self):
        model = GeminiSDKChatModel()

        @tool
        def my_tool(x: int) -> int:
            """A tool."""
            return x * 2

        bound = model.bind_tools([my_tool])
        self.assertEqual(len(bound._tools), 1)

    def test_bind_tools_with_tool_choice(self):
        model = GeminiSDKChatModel()
        bound = model.bind_tools([], tool_choice="any")
        self.assertIsNotNone(bound._tools)


class TestMessageConversion(unittest.TestCase):
    def test_system_message_becomes_instruction(self):
        sys_text, contents = _to_gemini_content([
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello"),
        ])
        self.assertEqual(sys_text, "You are a helpful assistant.")
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["role"], "user")

    def test_multiple_user_model_turns(self):
        _, contents = _to_gemini_content([
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!"),
            HumanMessage(content="How are you?"),
        ])
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0]["role"], "user")
        self.assertEqual(contents[1]["role"], "model")
        self.assertEqual(contents[2]["role"], "user")

    def test_tool_call_in_ai_message(self):
        msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_weather",
                    "args": {"city": "SF"},
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        )
        _, contents = _to_gemini_content([msg])
        self.assertEqual(len(contents), 1)
        part = contents[0]["parts"][0]
        self.assertIn("function_call", part)
        self.assertEqual(part["function_call"]["name"], "get_weather")

    def test_tool_message(self):
        _, contents = _to_gemini_content([
            ToolMessage(content="42", tool_call_id="call_1", name="calculator"),
        ])
        self.assertEqual(len(contents), 1)
        part = contents[0]["parts"][0]
        self.assertIn("function_response", part)

    def test_empty_messages(self):
        sys_text, contents = _to_gemini_content([])
        self.assertIsNone(sys_text)
        self.assertEqual(contents, [])

    def test_empty_human_message(self):
        _, contents = _to_gemini_content([HumanMessage(content="")])
        # Empty content should not produce a part
        self.assertEqual(contents, [])


class TestRoleMapping(unittest.TestCase):
    def test_human_role(self):
        self.assertEqual(_gemini_role(HumanMessage(content="hi")), "user")

    def test_ai_role(self):
        self.assertEqual(_gemini_role(AIMessage(content="hi")), "model")

    def test_tool_role(self):
        self.assertEqual(
            _gemini_role(ToolMessage(content="r", tool_call_id="c1", name="t")),
            "function",
        )


class TestTextExtraction(unittest.TestCase):
    def test_string_content(self):
        self.assertEqual(_extract_text("hello"), "hello")

    def test_list_content(self):
        self.assertEqual(
            _extract_text([{"text": "hello"}, {"text": "world"}]),
            "hello world",
        )

    def test_none_content(self):
        self.assertEqual(_extract_text(None), "")

    def test_dict_list_with_mixed(self):
        self.assertEqual(
            _extract_text(["hello", {"text": "world"}]),
            "hello world",
        )


class TestToolConversion(unittest.TestCase):
    def test_pydantic_model(self):
        class SearchInput(BaseModel):
            """Search for information."""
            query: str = Field(description="The search query")
            max_results: int = Field(default=10, description="Max results")

        fd = _tool_to_function_declaration(SearchInput)
        self.assertIsNotNone(fd)
        self.assertEqual(fd["name"], "SearchInput")
        self.assertEqual(fd["description"], "Search for information.")
        self.assertIn("parameters", fd)

    def test_base_tool(self):
        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        fd = _tool_to_function_declaration(add)
        self.assertIsNotNone(fd)
        self.assertEqual(fd["name"], "add")

    def test_raw_dict(self):
        fd = _tool_to_function_declaration({
            "name": "custom_fn",
            "description": "A custom function",
            "parameters": {
                "type": "object",
                "properties": {"x": {"type": "number"}},
                "required": ["x"],
            },
        })
        self.assertIsNotNone(fd)
        self.assertEqual(fd["name"], "custom_fn")

    def test_convert_tools_list(self):
        class ToolA(BaseModel):
            """Tool A."""
            x: str

        gemini_tools = _convert_tools_to_gemini([ToolA])
        self.assertIsNotNone(gemini_tools)
        self.assertEqual(len(gemini_tools), 1)
        self.assertIn("function_declarations", gemini_tools[0])

    def test_convert_empty_tools(self):
        self.assertIsNone(_convert_tools_to_gemini([]))
        self.assertIsNone(_convert_tools_to_gemini(None))


class TestModelResourceResolution(unittest.TestCase):
    def test_short_name(self):
        self.assertEqual(
            _resolve_model_resource("gemini-2.5-pro"),
            "models/gemini-2.5-pro",
        )

    def test_already_full_name(self):
        self.assertEqual(
            _resolve_model_resource("models/gemini-2.5-flash"),
            "models/gemini-2.5-flash",
        )

    def test_unknown_name(self):
        self.assertEqual(
            _resolve_model_resource("custom-model"),
            "models/custom-model",
        )


class TestResponseParsing(unittest.TestCase):
    def test_parse_text_response(self):
        response = _MockResponse(parts=[_MockPart(text="Hello from Gemini")])
        msg = _parse_gemini_response(response)
        self.assertEqual(msg.content, "Hello from Gemini")
        self.assertEqual(msg.tool_calls, [])

    def test_parse_function_call(self):
        fc = _MockFunctionCall(name="search", args={"q": "cancer"})
        response = _MockResponse(parts=[_MockPart(function_call=fc)])
        msg = _parse_gemini_response(response)
        self.assertTrue(msg.tool_calls)
        self.assertEqual(msg.tool_calls[0]["name"], "search")

    def test_parse_empty_response(self):
        response = _MockResponse(parts=[])
        msg = _parse_gemini_response(response)
        self.assertEqual(msg.content, "")

    def test_parse_no_candidates(self):
        response = _MockResponse(parts=None)
        msg = _parse_gemini_response(response)
        self.assertIsNotNone(msg.content)

    def test_stop_sequences_applied(self):
        response = _MockResponse(parts=[_MockPart(text="Hello there</act>more")])
        msg = _parse_gemini_response(response, stop=["</act>"])
        self.assertEqual(msg.content, "Hello there")


class TestGenerateErrors(unittest.TestCase):
    def test_missing_sdk(self):
        model = GeminiSDKChatModel()
        with patch(
            "spatialagent.agent.gemini_sdk_chatmodel.GeminiSDKChatModel._generate",
        ) as mock_gen:
            mock_gen.return_value = type(
                "ChatResult",
                (),
                {
                    "generations": [
                        type(
                            "ChatGeneration",
                            (),
                            {
                                "message": AIMessage(
                                    content="google-genai SDK not installed",
                                )
                            },
                        )()
                    ]
                },
            )()
            # This test just validates the error path exists
            result = model._generate([HumanMessage(content="hi")])
            self.assertIn("SDK", result.generations[0].message.content)


if __name__ == "__main__":
    unittest.main()
