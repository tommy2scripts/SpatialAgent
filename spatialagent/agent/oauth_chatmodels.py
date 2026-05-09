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
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
        except subprocess.TimeoutExpired:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content=f"ERROR: codex timed out after {self.timeout}s")
                )]
            )
        except FileNotFoundError:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content="ERROR: codex CLI not found. Install with: npm install -g @openai/codex")
                )]
            )

        text = (
            result.stdout.strip()
            if result.returncode == 0
            else f"ERROR: {result.stderr}"
        )

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=text))]
        )


class GeminiOAuthChatModel(BaseChatModel):
    """LangChain ChatModel wrapping Gemini CLI via OAuth."""

    model: str = "gemini-3-pro-preview"
    timeout: int = 300

    @property
    def _llm_type(self) -> str:
        return "gemini-oauth"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = messages[-1].content if messages else ""

        cmd = [
            "gemini",
            "--prompt", prompt,
            "--output-format", "json",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
        except subprocess.TimeoutExpired:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content=f"ERROR: gemini timed out after {self.timeout}s")
                )]
            )
        except FileNotFoundError:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content="ERROR: gemini CLI not found. Install with: npm install -g @google/gemini-cli")
                )]
            )

        if result.returncode == 0:
            try:
                import json
                parsed = json.loads(result.stdout)
                text = parsed.get("response", result.stdout.strip())
            except json.JSONDecodeError:
                text = result.stdout.strip()
        else:
            text = f"ERROR: {result.stderr}"

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=text))]
        )
