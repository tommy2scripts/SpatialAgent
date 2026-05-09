"""
Tests for SpatialAgent model routing and external coding-agent tools.

Covers:
- Model routing logic (OpenAI, Azure, Anthropic, Gemini, OpenRouter, z.AI, local)
- Gemini API key isolation (never reuses generic/OpenAI keys)
- External coding agent tool structure and error handling
"""

import os
import sys
import tempfile
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# =============================================================================
# Test: Gemini API key isolation
# =============================================================================

class TestGeminiAPIKeyIsolation(unittest.TestCase):
    """Verify that gemini/ model routing never reuses generic or OpenAI API keys."""

    def setUp(self):
        # Save original environment
        self._original_env = {}
        for key in [
            "GEMINI_API_KEY", "GOOGLE_API_KEY",
            "CUSTOM_LLM_API_KEY", "CUSTOM_MODEL_API_KEY",
            "OPENAI_API_KEY", "OPENROUTER_API_KEY",
            "CUSTOM_LLM_BASE_URL", "CUSTOM_MODEL_BASE_URL", "OPENAI_BASE_URL",
            "OPENCODE_GO_API_KEY", "OPENCODE_GO_BASE_URL",
        ]:
            self._original_env[key] = os.environ.get(key)

    def tearDown(self):
        # Restore original environment
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _clear_all_api_keys(self):
        """Remove all API key env vars."""
        for key in [
            "GEMINI_API_KEY", "GOOGLE_API_KEY",
            "CUSTOM_LLM_API_KEY", "CUSTOM_MODEL_API_KEY",
            "OPENAI_API_KEY", "OPENROUTER_API_KEY",
            "OPENCODE_GO_API_KEY",
        ]:
            os.environ.pop(key, None)

    def test_gemini_prefix_does_not_reuse_generic_api_keys(self):
        """gemini/ models must NOT fall back to CUSTOM_LLM_API_KEY or OPENAI_API_KEY.

        This was a security issue: make_llm("gemini/...") could route to Google's
        OpenAI-compatible endpoint while sending a generic or OpenAI key.
        """
        self._clear_all_api_keys()

        # Set generic/OpenAI keys that should NOT be used for Gemini
        os.environ["CUSTOM_LLM_API_KEY"] = "sk-generic-secret-key"
        os.environ["OPENAI_API_KEY"] = "sk-openai-secret-key"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("gemini-3-pro-preview", track_cost=False)

            # Verify ChatOpenAI was called
            call_kwargs = mock_chat.call_args.kwargs

            # api_key must be "EMPTY" -- never the generic or OpenAI key
            api_key = call_kwargs.get("api_key")
            self.assertEqual(
                api_key, "EMPTY",
                f"Gemini routing leaked a non-Gemini API key: {api_key!r}. "
                "It should be 'EMPTY' when no GEMINI_API_KEY or GOOGLE_API_KEY is set."
            )

    def test_gemini_uses_gemini_api_key_when_set(self):
        """When GEMINI_API_KEY is set, Gemini routing should use it."""
        self._clear_all_api_keys()
        os.environ["GEMINI_API_KEY"] = "sk-gemini-123"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm

            make_llm("gemini-3-pro-preview", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("api_key"), "sk-gemini-123")

    def test_gemini_uses_google_api_key_as_fallback(self):
        """When GEMINI_API_KEY is not set but GOOGLE_API_KEY is, use GOOGLE_API_KEY."""
        self._clear_all_api_keys()
        os.environ["GOOGLE_API_KEY"] = "sk-google-456"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm

            make_llm("gemini-2.5-pro", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("api_key"), "sk-google-456")

    def test_gemini_prefers_gemini_key_over_google_key(self):
        """When both GEMINI_API_KEY and GOOGLE_API_KEY are set, prefer GEMINI_API_KEY."""
        self._clear_all_api_keys()
        os.environ["GEMINI_API_KEY"] = "sk-gemini-priority"
        os.environ["GOOGLE_API_KEY"] = "sk-google-fallback"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm

            make_llm("gemini-3-flash-preview", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("api_key"), "sk-gemini-priority")

    def test_gemini_uses_correct_base_url(self):
        """Gemini routing must use Google's OpenAI-compatible endpoint."""
        self._clear_all_api_keys()
        os.environ["GEMINI_API_KEY"] = "sk-test"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm

            make_llm("gemini-3-pro-preview", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(
                call_kwargs.get("base_url"),
                "https://generativelanguage.googleapis.com/v1beta/openai/"
            )

    def test_gemini_routing_ignores_generic_openai_base_url(self):
        """Gemini models must not be captured by generic OpenAI-compatible env vars."""
        self._clear_all_api_keys()
        os.environ["GEMINI_API_KEY"] = "sk-gemini"
        os.environ["OPENAI_API_KEY"] = "sk-openai-should-not-leak"
        os.environ["OPENAI_BASE_URL"] = "https://generic.example/v1"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("gemini-3-pro-preview", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("api_key"), "sk-gemini")
            self.assertEqual(
                call_kwargs.get("base_url"),
                "https://generativelanguage.googleapis.com/v1beta/openai/"
            )

    def test_gemini_name_with_opencode_substring_does_not_use_opencode_key(self):
        """A Gemini-looking model name must not route to OpenCode Go by substring."""
        self._clear_all_api_keys()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-should-not-leak"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("gemini-opencode-go", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("api_key"), "EMPTY")
            self.assertEqual(
                call_kwargs.get("base_url"),
                "https://generativelanguage.googleapis.com/v1beta/openai/"
            )


# =============================================================================
# Test: OpenAI-compatible routing
# =============================================================================

class TestOpenAICompatibleRouting(unittest.TestCase):
    """Test routing for OpenAI-compatible providers."""

    def setUp(self):
        self._original_env = {}
        for key in [
            "CUSTOM_LLM_BASE_URL", "CUSTOM_MODEL_BASE_URL", "OPENAI_BASE_URL",
            "CUSTOM_LLM_API_KEY", "CUSTOM_MODEL_API_KEY", "OPENAI_API_KEY",
            "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_HTTP_REFERER",
            "OPENROUTER_APP_TITLE",
            "ZAI_API_KEY", "ZAI_BASE_URL",
            "OPENCODE_GO_API_KEY", "OPENCODE_GO_BASE_URL", "OPENCODE_GO_MODEL",
            "LOCAL_LLM_BASE_URL", "LOCAL_LLM_API_KEY",
            "SPATIALAGENT_MAX_TOKENS", "SPATIALAGENT_REASONING_MAX_TOKENS",
        ]:
            self._original_env[key] = os.environ.get(key)

    def tearDown(self):
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _clear(self):
        for key in [
            "CUSTOM_LLM_BASE_URL", "CUSTOM_MODEL_BASE_URL", "OPENAI_BASE_URL",
            "CUSTOM_LLM_API_KEY", "CUSTOM_MODEL_API_KEY", "OPENAI_API_KEY",
            "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL",
            "ZAI_API_KEY", "ZAI_BASE_URL",
            "OPENCODE_GO_API_KEY", "OPENCODE_GO_BASE_URL", "OPENCODE_GO_MODEL",
            "LOCAL_LLM_BASE_URL", "LOCAL_LLM_API_KEY",
            "SPATIALAGENT_MAX_TOKENS", "SPATIALAGENT_REASONING_MAX_TOKENS",
        ]:
            os.environ.pop(key, None)

    def test_openrouter_prefix_resolves_model_name(self):
        """openrouter/ prefix should strip prefix and set correct base URL."""
        self._clear()
        os.environ["OPENROUTER_API_KEY"] = "sk-or-key"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("openrouter/anthropic/claude-sonnet-4-5")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "anthropic/claude-sonnet-4-5")
        self.assertEqual(base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(api_key, "sk-or-key")

    def test_zai_prefix_resolves_model_name(self):
        """zai/ prefix should strip prefix and set correct base URL."""
        self._clear()
        os.environ["ZAI_API_KEY"] = "sk-zai-key"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("zai/glm-4.6")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "glm-4.6")
        self.assertEqual(base_url, "https://api.z.ai/api/paas/v4")
        self.assertEqual(api_key, "sk-zai-key")

    def test_local_prefix_resolves_model_name(self):
        """local/ prefix should strip prefix and set correct base URL."""
        self._clear()
        os.environ["LOCAL_LLM_BASE_URL"] = "http://localhost:8080/v1"
        os.environ["LOCAL_LLM_API_KEY"] = "sk-local-key"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("local/llama3.1:70b")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "llama3.1:70b")
        self.assertEqual(base_url, "http://localhost:8080/v1")
        self.assertEqual(api_key, "sk-local-key")

    def test_strip_provider_prefix_helper(self):
        """Provider prefix stripping should return the suffix and reject empty suffixes."""
        from spatialagent.agent.make_llm import _strip_provider_prefix

        self.assertEqual(
            _strip_provider_prefix("openrouter/anthropic/claude-sonnet-4-5", "openrouter/"),
            "anthropic/claude-sonnet-4-5",
        )
        with self.assertRaises(ValueError):
            _strip_provider_prefix("openrouter/", "openrouter/")

    def test_native_provider_model_detection(self):
        """Native model families should not be captured by generic compatible gateways."""
        from spatialagent.agent.make_llm import _is_native_provider_model

        self.assertTrue(_is_native_provider_model("gemini-3-pro-preview"))
        self.assertTrue(_is_native_provider_model("claude-sonnet-4-5-20250929"))
        self.assertTrue(_is_native_provider_model("us.anthropic.claude-sonnet-4-5-20250929-v1:0"))
        self.assertFalse(_is_native_provider_model("opencode-go/kimi-k2.6"))
        self.assertFalse(_is_native_provider_model("openrouter/anthropic/claude-sonnet-4-5"))

    def test_opencode_go_prefix_resolves_model_name_and_key(self):
        """opencode-go/ prefix should use its provider endpoint and key."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go/deepseek-v4-pro")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "deepseek-v4-pro")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-opencode-go-key")

    def test_opencode_go_can_fall_back_to_openrouter_key(self):
        """OpenCode Go deployments commonly reuse OPENROUTER_API_KEY."""
        self._clear()
        os.environ["OPENROUTER_API_KEY"] = "sk-openrouter-fallback"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go/qwen3.6-plus")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "qwen3.6-plus")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-openrouter-fallback")

    def test_opencode_go_bare_prefix_uses_non_reasoning_default_model(self):
        """Bare opencode-go should pick a non-reasoning default model."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "kimi-k2.6")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-opencode-go-key")

    def test_opencode_go_bare_alias_respects_model_env_override(self):
        """Bare opencode-go should allow OPENCODE_GO_MODEL to select the backend."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"
        os.environ["OPENCODE_GO_MODEL"] = "qwen3.6-plus"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "qwen3.6-plus")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-opencode-go-key")

    def test_opencode_go_key_takes_precedence_over_openrouter_key(self):
        """Explicit OpenCode Go credentials should win when both key env vars exist."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"
        os.environ["OPENROUTER_API_KEY"] = "sk-openrouter-fallback"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go/kimi-k2.6")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "kimi-k2.6")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-opencode-go-key")

    def test_explicit_provider_prefix_ignores_generic_openai_base_url(self):
        """Generic OpenAI-compatible env vars must not hijack explicit provider prefixes."""
        self._clear()
        os.environ["OPENAI_BASE_URL"] = "https://generic.example/v1"
        os.environ["OPENAI_API_KEY"] = "sk-generic"
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go/kimi-k2.6")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "kimi-k2.6")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-opencode-go-key")

    def test_opencode_go_prefix_wins_over_gemini_substring(self):
        """Explicit opencode-go/ routing must win even if the backend model name says gemini."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"
        os.environ["GEMINI_API_KEY"] = "sk-gemini-should-not-leak"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("opencode-go/gemini-opencode-go")
        self.assertIsNotNone(result)
        resolved_model, base_url, api_key, headers = result
        self.assertEqual(resolved_model, "gemini-opencode-go")
        self.assertEqual(base_url, "https://opencode.ai/zen/go/v1")
        self.assertEqual(api_key, "sk-opencode-go-key")

    def test_native_claude_ignores_generic_openai_base_url(self):
        """Claude models should stay on the Anthropic path when generic base URL exists."""
        self._clear()
        os.environ["OPENAI_BASE_URL"] = "https://generic.example/v1"
        os.environ["OPENAI_API_KEY"] = "sk-openai-should-not-leak"

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        self.assertIsNone(_resolve_openai_compatible_routing("claude-sonnet-4-5-20250929"))

    def test_provider_prefix_requires_model_name(self):
        """Provider prefixes without model names should fail before constructing an LLM."""
        self._clear()

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        with self.assertRaises(ValueError):
            _resolve_openai_compatible_routing("opencode-go/")

    def test_no_custom_base_url_returns_none(self):
        """Without any custom base URL, routing should return None (fall through to providers)."""
        self._clear()

        from spatialagent.agent.make_llm import _resolve_openai_compatible_routing

        result = _resolve_openai_compatible_routing("gpt-4o")
        self.assertIsNone(result)

    def test_reasoning_content_model_detection(self):
        """Known reasoning-content models should be detected before LLM construction."""
        from spatialagent.agent.make_llm import _is_reasoning_content_model

        self.assertTrue(_is_reasoning_content_model("deepseek-v4-flash"))
        self.assertTrue(_is_reasoning_content_model("deepseek-r1"))
        self.assertFalse(_is_reasoning_content_model("kimi-k2.6"))

    def test_default_reasoning_max_tokens_env_override(self):
        """Reasoning max-token fallback should be env-configurable and robust."""
        from spatialagent.agent.make_llm import _default_reasoning_max_tokens

        self._clear()
        os.environ["SPATIALAGENT_REASONING_MAX_TOKENS"] = "49152"
        self.assertEqual(_default_reasoning_max_tokens(), 49152)

        os.environ["SPATIALAGENT_REASONING_MAX_TOKENS"] = "not-an-int"
        self.assertEqual(_default_reasoning_max_tokens(), 65536)

        os.environ["SPATIALAGENT_REASONING_MAX_TOKENS"] = "-1"
        self.assertEqual(_default_reasoning_max_tokens(), 65536)

    def test_default_max_tokens_env_parsing(self):
        """SPATIALAGENT_MAX_TOKENS should accept positive ints and ignore bad values."""
        from spatialagent.agent.make_llm import _default_max_tokens

        self._clear()
        os.environ["SPATIALAGENT_MAX_TOKENS"] = "24576"
        self.assertEqual(_default_max_tokens(), 24576)

        os.environ["SPATIALAGENT_MAX_TOKENS"] = "not-an-int"
        self.assertEqual(_default_max_tokens(), 393216)

        os.environ["SPATIALAGENT_MAX_TOKENS"] = "0"
        self.assertEqual(_default_max_tokens(), 393216)

    def test_opencode_go_reasoning_model_gets_larger_default_token_budget(self):
        """deepseek-v4-flash needs extra completion budget for reasoning_content."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("opencode-go/deepseek-v4-flash", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("model"), "deepseek-v4-flash")
            self.assertEqual(call_kwargs.get("max_tokens"), 65536)

    def test_opencode_go_reasoning_model_respects_explicit_token_budget(self):
        """Explicit max_tokens should override the protective default."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("opencode-go/deepseek-v4-flash", max_tokens=65536, track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("max_tokens"), 65536)

    def test_opencode_go_non_reasoning_model_uses_default_token_budget(self):
        """Non-reasoning OpenCode Go models should use the global completion budget."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("opencode-go/kimi-k2.6", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("max_tokens"), 393216)

    def test_opencode_go_non_reasoning_model_respects_max_tokens_env_override(self):
        """SPATIALAGENT_MAX_TOKENS should affect OpenAI-compatible non-reasoning calls."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"
        os.environ["SPATIALAGENT_MAX_TOKENS"] = "24576"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("opencode-go/kimi-k2.6", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("max_tokens"), 24576)

    def test_opencode_go_non_reasoning_model_ignores_invalid_max_tokens_env(self):
        """Invalid SPATIALAGENT_MAX_TOKENS values should not break LLM construction."""
        self._clear()
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"
        os.environ["SPATIALAGENT_MAX_TOKENS"] = "not-an-int"

        with patch("spatialagent.agent.make_llm.ChatOpenAI") as mock_chat:
            mock_chat.return_value = MagicMock()

            from spatialagent.agent.make_llm import make_llm
            make_llm("opencode-go/kimi-k2.6", track_cost=False)

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("max_tokens"), 393216)


# =============================================================================
# Test: Bedrock model detection
# =============================================================================

class TestBedrockModelDetection(unittest.TestCase):
    """Test AWS Bedrock model prefix detection."""

    def test_standard_bedrock_prefix(self):
        from spatialagent.agent.make_llm import _is_bedrock_model
        self.assertTrue(_is_bedrock_model("anthropic.claude-sonnet-4-5-20250929-v1:0"))

    def test_cross_region_bedrock_prefix(self):
        from spatialagent.agent.make_llm import _is_bedrock_model
        self.assertTrue(_is_bedrock_model("us.anthropic.claude-sonnet-4-5-20250929-v1:0"))

    def test_non_bedrock_model(self):
        from spatialagent.agent.make_llm import _is_bedrock_model
        self.assertFalse(_is_bedrock_model("gpt-4o"))
        self.assertFalse(_is_bedrock_model("claude-sonnet-4-5-20250929"))
        self.assertFalse(_is_bedrock_model("gemini-3-pro-preview"))


# =============================================================================
# Test: Cost callback
# =============================================================================

class TestCostCallback(unittest.TestCase):
    """Test cost tracking for LLM calls."""

    def test_cost_callback_initialization(self):
        from spatialagent.agent.make_llm import CostCallback

        cb = CostCallback("gpt-4o")
        self.assertEqual(cb.model, "gpt-4o")
        self.assertEqual(cb.total_cost, 0.0)
        self.assertEqual(cb.total_tokens, {"input": 0, "output": 0})
        self.assertEqual(cb.num_calls, 0)

    def test_cost_calculation_known_model(self):
        from spatialagent.agent.make_llm import CostCallback

        cb = CostCallback("gpt-4o")
        # gpt-4o: $2.50 input, $10.00 output per 1M tokens

        # Simulate an LLM response with token usage
        mock_response = MagicMock()
        mock_response.llm_output = {"token_usage": {"prompt_tokens": 1000, "completion_tokens": 500}}

        cb.on_llm_end(mock_response)

        expected_cost = (1000 * 2.50 / 1_000_000) + (500 * 10.00 / 1_000_000)
        self.assertAlmostEqual(cb.total_cost, expected_cost)
        self.assertEqual(cb.num_calls, 1)
        self.assertEqual(cb.total_tokens["input"], 1000)
        self.assertEqual(cb.total_tokens["output"], 500)

    def test_cost_unknown_model_uses_default_rate(self):
        from spatialagent.agent.make_llm import CostCallback

        cb = CostCallback("unknown-model")
        # Default rate: $2.00 input, $2.00 output per 1M tokens
        self.assertEqual(cb.rates, {"input": 2.0, "output": 2.0})


# =============================================================================
# Test: External coding agent tools
# =============================================================================

class TestExternalCodingAgentTools(unittest.TestCase):
    """Test external coding agent tool structure and error handling."""

    def test_delegate_to_claude_code_importable(self):
        """Verify the tool can be imported."""
        from spatialagent.tool.coding import delegate_to_claude_code
        self.assertTrue(hasattr(delegate_to_claude_code, "invoke"))

    def test_delegate_to_codex_importable(self):
        """Verify the tool can be imported."""
        from spatialagent.tool.coding import delegate_to_codex
        self.assertTrue(hasattr(delegate_to_codex, "invoke"))

    def test_delegate_to_opencode_importable(self):
        """Verify the tool can be imported."""
        from spatialagent.tool.coding import delegate_to_opencode
        self.assertTrue(hasattr(delegate_to_opencode, "invoke"))

    def test_run_external_agent_file_not_found(self):
        """Test graceful handling when CLI is not installed."""
        from spatialagent.tool.coding import _run_external_agent

        result = _run_external_agent("nonexistent-cli-xyz", "test task", timeout=5)
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"].lower())

    def test_run_external_agent_timeout(self):
        """Test graceful handling of timeout."""
        from spatialagent.tool.coding import _run_external_agent

        # Use 'sleep' as a command that will timeout
        result = _run_external_agent("sleep", "10", timeout=1)
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"].lower())

    def test_run_external_agent_success_mock(self):
        """Test successful execution with mocked subprocess."""
        from spatialagent.tool.coding import _run_external_agent

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Task completed successfully"
        mock_result.stderr = ""

        with patch("spatialagent.tool.coding.subprocess.run", return_value=mock_result) as mock_run:
            result = _run_external_agent("claude", "test task", timeout=300)

            self.assertTrue(result["success"])
            self.assertIn("Task completed successfully", result["output"])
            self.assertIsNone(result["error"])

            # Verify the command was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            self.assertEqual(call_args.args[0], ["claude", "--print", "test task"])

    def test_agent_command_builders(self):
        """Supported co-agent commands should build argv without shell splitting."""
        from spatialagent.tool.coding import _build_external_agent_command

        self.assertEqual(
            _build_external_agent_command("claude", "test task"),
            ["claude", "--print", "test task"],
        )
        self.assertEqual(
            _build_external_agent_command("codex", "test task"),
            ["codex", "exec", "--skip-git-repo-check", "-m", "gpt-5.5", "test task"],
        )
        self.assertEqual(
            _build_external_agent_command("opencode", "test task"),
            ["opencode", "run", "test task"],
        )
        self.assertEqual(
            _build_external_agent_command(["custom-agent", "--flag"], "test task"),
            ["custom-agent", "--flag", "test task"],
        )

    def test_agent_command_registry_covers_supported_clis(self):
        """The command registry should explicitly cover each public delegate CLI."""
        from spatialagent.tool.coding import _AGENT_COMMANDS

        self.assertEqual(set(_AGENT_COMMANDS), {"claude", "codex", "opencode"})
        self.assertEqual(_AGENT_COMMANDS["claude"]("task"), ["claude", "--print", "task"])
        self.assertEqual(_AGENT_COMMANDS["opencode"]("task"), ["opencode", "run", "task"])

        with patch.dict(os.environ, {"CODEX_MODEL": "gpt-5-codex"}, clear=False):
            self.assertEqual(
                _AGENT_COMMANDS["codex"]("task"),
                ["codex", "exec", "--skip-git-repo-check", "-m", "gpt-5-codex", "task"],
            )

    def test_agent_command_builder_rejects_empty_sequence(self):
        """Empty argv prefixes should fail before subprocess execution."""
        from spatialagent.tool.coding import _build_external_agent_command

        with self.assertRaises(ValueError):
            _build_external_agent_command([], "test task")

    def test_run_external_agent_codex_uses_exec_command(self):
        """Codex CLI should use non-interactive codex exec, not Claude's --print flag."""
        from spatialagent.tool.coding import _run_external_agent

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "done"
        mock_result.stderr = ""

        with patch("spatialagent.tool.coding.subprocess.run", return_value=mock_result) as mock_run:
            result = _run_external_agent("codex", "test task", timeout=300)

            self.assertTrue(result["success"])
            call_args = mock_run.call_args
            self.assertEqual(
                call_args.args[0],
                ["codex", "exec", "--skip-git-repo-check", "-m", "gpt-5.5", "test task"],
            )

    def test_run_external_agent_opencode_uses_run_command(self):
        """OpenCode CLI should use opencode run, not Claude's --print flag."""
        from spatialagent.tool.coding import _run_external_agent

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "done"
        mock_result.stderr = ""

        with patch("spatialagent.tool.coding.subprocess.run", return_value=mock_result) as mock_run:
            result = _run_external_agent("opencode", "test task", timeout=300)

            self.assertTrue(result["success"])
            call_args = mock_run.call_args
            self.assertEqual(call_args.args[0], ["opencode", "run", "test task"])

    def test_run_external_agent_failure(self):
        """Test handling of non-zero exit code."""
        from spatialagent.tool.coding import _run_external_agent

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: something went wrong"

        with patch("spatialagent.tool.coding.subprocess.run", return_value=mock_result):
            result = _run_external_agent("claude", "test task", timeout=300)

            self.assertFalse(result["success"])
            self.assertIn("Exit code 1", result["error"])

    def test_format_external_agent_result_success(self):
        """Successful co-agent output should be returned without an ERROR marker."""
        from spatialagent.tool.coding import _format_external_agent_result

        result = _format_external_agent_result(
            "Codex",
            {"success": True, "output": "changed tests", "error": None},
        )

        self.assertEqual(result, "Codex completed the task:\n\nchanged tests")
        self.assertNotIn("ERROR:", result)

    def test_format_external_agent_result_failure(self):
        """Failed co-agent output should include a visible ERROR marker and stdout."""
        from spatialagent.tool.coding import _format_external_agent_result

        result = _format_external_agent_result(
            "OpenCode",
            {"success": False, "output": "partial output", "error": "Exit code 1"},
        )

        self.assertIn("ERROR: OpenCode failed: Exit code 1", result)
        self.assertIn("Output:\npartial output", result)
        self.assertIn("The co-agent task did not complete", result)

    def test_delegate_failure_is_marked_as_observable_error(self):
        """Delegate tools should return an ERROR string that survives the act observation."""
        from spatialagent.tool.coding import delegate_to_codex

        with patch("spatialagent.tool.coding._run_external_agent") as mock_run:
            mock_run.return_value = {
                "success": False,
                "output": "",
                "error": "Agent timed out after 1s",
            }

            result = delegate_to_codex.invoke({"task": "test task", "timeout": 1})

            self.assertIn("ERROR: Codex failed", result)
            self.assertIn("Agent timed out after 1s", result)
            self.assertIn("The co-agent task did not complete", result)

    def test_delegate_tools_register_with_tool_executor(self):
        """Delegate tools should be executable through the same registry path as LangGraph acts."""
        from spatialagent.agent.tool_system import ToolRegistry, ToolExecutor
        from spatialagent.tool.coding import delegate_to_codex

        registry = ToolRegistry()
        registry.register_langchain_tool(delegate_to_codex)
        executor = ToolExecutor(registry)

        with patch("spatialagent.tool.coding._run_external_agent") as mock_run:
            mock_run.return_value = {
                "success": False,
                "output": "",
                "error": "codex not found",
            }

            result = executor.execute_tool("delegate_to_codex", task="test task", timeout=1)

            self.assertIsInstance(result, str)
            self.assertIn("ERROR: Codex failed", result)

    def test_spatialagent_observation_failure_detector_catches_delegate_error(self):
        """The LangGraph loop should be able to mark ERROR observations as failed actions."""
        from spatialagent.agent.spatialagent import SpatialAgent

        self.assertTrue(
            SpatialAgent._observation_indicates_failure(
                "Result: 'ERROR: Codex failed: codex not found'"
            )
        )

    def test_spatialagent_observation_failure_detector_ignores_success_text(self):
        """Normal observations and non-string results should not be marked as failures."""
        from spatialagent.agent.spatialagent import SpatialAgent

        self.assertFalse(SpatialAgent._observation_indicates_failure("Codex completed the task"))
        self.assertFalse(SpatialAgent._observation_indicates_failure({"error": "not a string"}))


# =============================================================================
# Test: SpatialAgent integration with routed models
# =============================================================================

class TestSpatialAgentModelIntegration(unittest.TestCase):
    """Test that routed LLMs keep the resolved model name when installed in SpatialAgent."""

    def setUp(self):
        self._original_env = {}
        for key in [
            "OPENCODE_GO_API_KEY",
            "SPATIALAGENT_MAX_TOKENS",
            "SPATIALAGENT_REASONING_MAX_TOKENS",
        ]:
            self._original_env[key] = os.environ.get(key)

    def tearDown(self):
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_spatialagent_uses_resolved_opencode_go_model_name(self):
        """A make_llm("opencode-go/...") instance should register its backend model in the agent loop."""
        os.environ["OPENCODE_GO_API_KEY"] = "sk-opencode-go-key"

        llm = MagicMock()
        llm.model_name = "deepseek-v4-flash"
        llm.callbacks = []

        with patch("spatialagent.agent.make_llm.ChatOpenAI", return_value=llm) as mock_chat:
            from spatialagent.agent.make_llm import make_llm
            from spatialagent.agent.spatialagent import SpatialAgent
            from spatialagent.agent import get_agent_model

            routed_llm = make_llm("opencode-go/deepseek-v4-flash", track_cost=False)
            with tempfile.TemporaryDirectory() as tmpdir:
                agent = SpatialAgent(
                    llm=routed_llm,
                    tools=[],
                    data_path=os.path.join(tmpdir, "data"),
                    save_path=os.path.join(tmpdir, "experiments"),
                    tool_retrieval=False,
                    skill_retrieval=False,
                )

            call_kwargs = mock_chat.call_args.kwargs
            self.assertEqual(call_kwargs.get("model"), "deepseek-v4-flash")
            self.assertEqual(agent.llm, routed_llm)
            self.assertEqual(get_agent_model(), "deepseek-v4-flash")


# =============================================================================
# Test: Tool exports
# =============================================================================

class TestToolExports(unittest.TestCase):
    """Verify that new tools are properly exported from the tool package."""

    def test_delegate_tools_in_all(self):
        """External coding agent tools should be in __all__."""
        from spatialagent.tool import __all__

        self.assertIn("delegate_to_claude_code", __all__)
        self.assertIn("delegate_to_codex", __all__)
        self.assertIn("delegate_to_opencode", __all__)

    def test_delegate_tools_importable_from_package(self):
        """External coding agent tools should be importable from spatialagent.tool."""
        from spatialagent.tool import (
            delegate_to_claude_code,
            delegate_to_codex,
            delegate_to_opencode,
        )
        self.assertTrue(hasattr(delegate_to_claude_code, "invoke"))
        self.assertTrue(hasattr(delegate_to_codex, "invoke"))
        self.assertTrue(hasattr(delegate_to_opencode, "invoke"))


if __name__ == "__main__":
    unittest.main()
