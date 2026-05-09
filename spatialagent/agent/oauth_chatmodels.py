"""LangChain ChatModel wrappers for OAuth-authenticated CLI tools.

CodexOAuthChatModel: wraps `codex exec --json`
GeminiOAuthChatModel: wraps `gemini --prompt`
"""
import json
import re
import subprocess
from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


DEFAULT_CODEX_OAUTH_MODEL = "gpt-5.5"
DEFAULT_GEMINI_OAUTH_MODEL = "gemini-3-pro-preview"

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)(\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._~+/=-]+)"),
    re.compile(r"\b(sk-[A-Za-z0-9_-]{8,})\b"),
)


def _redact_secrets(text: str) -> str:
    """Remove common credentials from CLI output before surfacing errors."""
    redacted = text
    redacted = _SECRET_PATTERNS[0].sub(r"\1\2[REDACTED]", redacted)
    redacted = _SECRET_PATTERNS[1].sub(r"\1[REDACTED]", redacted)
    redacted = _SECRET_PATTERNS[2].sub("[REDACTED]", redacted)
    return redacted


def _message_content_to_text(content: Any) -> str:
    """Convert LangChain message content variants into plain prompt text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return "" if content is None else str(content)


def _messages_to_prompt(messages: List[BaseMessage]) -> str:
    """Serialize the full chat history for CLIs that accept one prompt string."""
    prompt_parts = []
    for message in messages:
        role = getattr(message, "type", message.__class__.__name__).replace("_", " ")
        content = _message_content_to_text(message.content)
        if content:
            prompt_parts.append(f"{role}: {content}")
    return "\n\n".join(prompt_parts)


def _apply_stop_sequences(text: str, stop: Optional[List[str]]) -> str:
    """Apply LangChain stop sequences client-side for CLI backends."""
    if not stop:
        return text
    earliest = min((text.find(seq) for seq in stop if seq and seq in text), default=-1)
    return text[:earliest] if earliest >= 0 else text


def _chat_result(text: str, stop: Optional[List[str]] = None) -> ChatResult:
    return ChatResult(
        generations=[
            ChatGeneration(message=AIMessage(content=_apply_stop_sequences(text, stop)))
        ]
    )


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def _extract_codex_jsonl_text(stdout: str) -> str:
    """Extract the final assistant text from known Codex JSONL event shapes."""
    final_text = ""
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        if not item and isinstance(event.get("response_item"), dict):
            item = event["response_item"]

        event_type = event.get("type")
        item_type = item.get("type")

        if event_type in {"item.completed", "response_item.completed"}:
            if item_type == "agent_message" and isinstance(item.get("text"), str):
                final_text = item["text"]
            elif item_type == "message" and item.get("role") == "assistant":
                text = _extract_text_from_content(item.get("content"))
                if text:
                    final_text = text
        elif event_type == "agent_message" and isinstance(event.get("text"), str):
            final_text = event["text"]
        elif event_type == "message" and event.get("role") == "assistant":
            text = _extract_text_from_content(event.get("content"))
            if text:
                final_text = text

    return final_text


class CodexOAuthChatModel(BaseChatModel):
    """LangChain ChatModel wrapping Codex CLI via OAuth (codex exec --json)."""

    model: str = DEFAULT_CODEX_OAUTH_MODEL
    timeout: int = 300

    @property
    def _llm_type(self) -> str:
        return "codex-oauth"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model": self.model, "timeout": self.timeout}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = _messages_to_prompt(messages)

        cmd = ["codex", "exec", "--json", "--model", self.model, "-"]
        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return _chat_result(f"ERROR: codex timed out after {self.timeout}s", stop)
        except FileNotFoundError:
            return _chat_result(
                "ERROR: codex CLI not found. Install with: npm install -g @openai/codex",
                stop,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return _chat_result(f"ERROR: failed to run codex CLI: {_redact_secrets(str(exc))}", stop)

        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or f"exit code {result.returncode}").strip()
            return _chat_result(
                f"ERROR: {_redact_secrets(error_text)}",
                stop,
            )

        text = _extract_codex_jsonl_text(result.stdout)

        if not text:
            text = result.stdout.strip()

        return _chat_result(text, stop)


class GeminiOAuthChatModel(BaseChatModel):
    """LangChain ChatModel wrapping Gemini CLI via OAuth."""

    model: str = DEFAULT_GEMINI_OAUTH_MODEL
    timeout: int = 300

    @property
    def _llm_type(self) -> str:
        return "gemini-oauth"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model": self.model, "timeout": self.timeout}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = _messages_to_prompt(messages)

        cmd = [
            "gemini",
            "--prompt", "",
            "--model", self.model,
            "--output-format", "json",
        ]
        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return _chat_result(f"ERROR: gemini timed out after {self.timeout}s", stop)
        except FileNotFoundError:
            return _chat_result(
                "ERROR: gemini CLI not found. Install with: npm install -g @google/gemini-cli",
                stop,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return _chat_result(f"ERROR: failed to run gemini CLI: {_redact_secrets(str(exc))}", stop)

        if result.returncode == 0:
            try:
                parsed = json.loads(result.stdout)
                if isinstance(parsed, dict):
                    if parsed.get("error"):
                        text = f"ERROR: {_redact_secrets(json.dumps(parsed['error'], ensure_ascii=False))}"
                    else:
                        text = parsed.get("response", result.stdout.strip())
                else:
                    text = result.stdout.strip()
            except json.JSONDecodeError:
                text = result.stdout.strip()
        else:
            error_text = (result.stderr or result.stdout or f"exit code {result.returncode}").strip()
            text = f"ERROR: {_redact_secrets(error_text)}"

        return _chat_result(text, stop)
