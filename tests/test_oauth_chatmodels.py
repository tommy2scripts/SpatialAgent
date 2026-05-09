"""
Tests for OAuth ChatModel backends: CodexOAuthChatModel and GeminiOAuthChatModel.
"""
import unittest
from unittest.mock import patch, MagicMock


class TestCodexOAuthChatModel(unittest.TestCase):
    def test_llm_type_is_codex_oauth(self):
        from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel
        model = CodexOAuthChatModel()
        self.assertEqual(model._llm_type, "codex-oauth")

    def test_generate_calls_codex_exec(self):
        from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel
        from langchain_core.messages import HumanMessage

        model = CodexOAuthChatModel()
        messages = [HumanMessage(content="Hello")]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello from Codex"
        mock_result.stderr = ""

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", return_value=mock_result) as mock_run:
            result = model._generate(messages)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("codex", args[0])
            self.assertIn("exec", args)
            self.assertEqual(result.generations[0].text, "Hello from Codex")


class TestGeminiOAuthChatModel(unittest.TestCase):
    def test_llm_type_is_gemini_oauth(self):
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        model = GeminiOAuthChatModel()
        self.assertEqual(model._llm_type, "gemini-oauth")

    def test_generate_calls_gemini_cli(self):
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        from langchain_core.messages import HumanMessage
        import json

        model = GeminiOAuthChatModel()
        messages = [HumanMessage(content="What is the meaning of life?")]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"response": "42 is the answer."})
        mock_result.stderr = ""

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", return_value=mock_result) as mock_run:
            result = model._generate(messages)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("gemini", args[0])
            self.assertNotIn("--prompt", args)
            self.assertIn("--output-format", args)
            self.assertIn("json", args)
            self.assertEqual(result.generations[0].text, "42 is the answer.")


class TestOAuthEdgeCases(unittest.TestCase):
    """Edge case tests for OAuth chat models: timeout, missing CLI, invalid JSON, empty messages."""

    def test_codex_handles_timeout_gracefully(self):
        """CodexOAuthChatModel handles subprocess.TimeoutExpired -> returns ERROR text."""
        import subprocess
        from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel
        from langchain_core.messages import HumanMessage

        model = CodexOAuthChatModel(timeout=1)
        messages = [HumanMessage(content="Test prompt")]

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["codex"], timeout=1)):
            result = model._generate(messages)
            self.assertIn("ERROR", result.generations[0].text)
            self.assertIn("timed out", result.generations[0].text.lower())

    def test_gemini_handles_file_not_found(self):
        """GeminiOAuthChatModel handles FileNotFoundError gracefully -> returns ERROR text."""
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        from langchain_core.messages import HumanMessage

        model = GeminiOAuthChatModel()
        messages = [HumanMessage(content="Test prompt")]

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", side_effect=FileNotFoundError("gemini not found")):
            result = model._generate(messages)
            self.assertIn("ERROR", result.generations[0].text)
            self.assertIn("not found", result.generations[0].text.lower())

    def test_gemini_handles_invalid_json(self):
        """GeminiOAuthChatModel handles invalid JSON in stdout -> falls back to raw text."""
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        from langchain_core.messages import HumanMessage

        model = GeminiOAuthChatModel()
        messages = [HumanMessage(content="Test prompt")]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "This is not valid JSON {{broken"
        mock_result.stderr = ""

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", return_value=mock_result):
            result = model._generate(messages)
            self.assertEqual(result.generations[0].text, "This is not valid JSON {{broken")

    def test_empty_messages_handled_gracefully(self):
        """Empty messages list -> handled gracefully (returns empty result, no crash)."""
        from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel, GeminiOAuthChatModel
        from langchain_core.messages import AIMessage

        # Test Codex with empty messages
        model = CodexOAuthChatModel()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", return_value=mock_result) as mock_run:
            result = model._generate([])
            mock_run.assert_called_once()
            # Should not crash; returns AIMessage with empty content
            self.assertIsInstance(result.generations[0].message, AIMessage)
            self.assertEqual(result.generations[0].text, "")

        # Test Gemini with empty messages
        model = GeminiOAuthChatModel()
        mock_result.returncode = 0
        mock_result.stdout = '{"response": ""}'
        mock_result.stderr = ""

        with patch("spatialagent.agent.oauth_chatmodels.subprocess.run", return_value=mock_result) as mock_run:
            result = model._generate([])
            mock_run.assert_called_once()
            self.assertIsInstance(result.generations[0].message, AIMessage)
            self.assertEqual(result.generations[0].text, "")


class TestMakeLlmOAuthRouting(unittest.TestCase):
    """Test that make_llm routes codex-oauth and gemini-oauth prefixes correctly."""

    def test_make_llm_codex_oauth_returns_chatmodel(self):
        from spatialagent.agent.make_llm import make_llm
        from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel
        result = make_llm("codex-oauth")
        self.assertIsInstance(result, CodexOAuthChatModel)
        self.assertEqual(result._llm_type, "codex-oauth")

    def test_make_llm_gemini_oauth_returns_chatmodel(self):
        from spatialagent.agent.make_llm import make_llm
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        result = make_llm("gemini-oauth")
        self.assertIsInstance(result, GeminiOAuthChatModel)
        self.assertEqual(result._llm_type, "gemini-oauth")

    def test_make_llm_oauth_not_hijacked_by_custom_base_url(self):
        from spatialagent.agent.make_llm import make_llm
        from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel, GeminiOAuthChatModel

        with patch.dict("os.environ", {
            "CUSTOM_LLM_BASE_URL": "http://localhost:9999",
            "OPENAI_BASE_URL": "http://localhost:8888",
        }):
            codex = make_llm("codex-oauth")
            codex_prefixed = make_llm("codex-oauth/gpt-5.5")
            gemini = make_llm("gemini-oauth")
            gemini_prefixed = make_llm("gemini-oauth/gemini-2.5-pro")

        self.assertIsInstance(codex, CodexOAuthChatModel)
        self.assertIsInstance(codex_prefixed, CodexOAuthChatModel)
        self.assertIsInstance(gemini, GeminiOAuthChatModel)
        self.assertIsInstance(gemini_prefixed, GeminiOAuthChatModel)

    def test_make_llm_oauth_prefix_selects_cli_model(self):
        from spatialagent.agent.make_llm import make_llm

        codex = make_llm("codex-oauth/gpt-5.5")
        gemini = make_llm("gemini-oauth/gemini-2.5-pro")

        self.assertEqual(codex.model, "gpt-5.5")
        self.assertEqual(gemini.model, "gemini-2.5-pro")

    def test_make_llm_oauth_prefix_requires_model_name(self):
        from spatialagent.agent.make_llm import make_llm

        with self.assertRaises(ValueError):
            make_llm("codex-oauth/")
        with self.assertRaises(ValueError):
            make_llm("gemini-oauth/")
