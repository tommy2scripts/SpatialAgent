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
