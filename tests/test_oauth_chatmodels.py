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

        with patch("subprocess.run", return_value=mock_result) as mock_run:
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

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = model._generate(messages)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("gemini", args[0])
            self.assertIn("--prompt", args)
            self.assertIn("--output-format", args)
            self.assertIn("json", args)
            self.assertEqual(result.generations[0].text, "42 is the answer.")
