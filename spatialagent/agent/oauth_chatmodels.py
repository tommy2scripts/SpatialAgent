"""LangChain ChatModel wrappers for OAuth-authenticated CLI tools.

CodexOAuthChatModel: wraps `codex exec --print`
GeminiOAuthChatModel: wraps `gemini --prompt`
"""
import subprocess
from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class CodexOAuthChatModel(BaseChatModel):
    """LangChain ChatModel wrapping Codex CLI via OAuth."""

    model: str = "gpt-5.5"
    timeout: int = 300

    @property
    def _llm_type(self) -> str:
        return "codex-oauth"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = messages[-1].content if messages else ""

        cmd = ["codex", "exec", "--print", "-m", self.model, prompt]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=self.timeout
        )

        text = (
            result.stdout.strip()
            if result.returncode == 0
            else f"ERROR: {result.stderr}"
        )

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=text))]
        )
