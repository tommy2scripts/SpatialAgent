# OAuth ChatModel Backends Implementation Plan

> **For Hermes:** Use subagent-driven-development with OpenCode Go models (TDD).

**Goal:** Add CodexOAuthChatModel and GeminiOAuthChatModel — LangChain ChatModel wrappers around `codex exec` and `gemini --prompt` CLI tools, authenticated via OAuth. Register in make_llm.py as `codex-oauth` and `gemini-oauth` prefixes. Keep OpenCode Go routing unchanged.

**Architecture:** Each ChatModel subclasses BaseChatModel, implements `_generate()` by shelling out to the CLI subprocess, parses the response, and returns ChatResult. Both follow the existing pattern: subprocess.run with timeout, capture stdout/stderr, handle errors gracefully.

**Tech Stack:** Python 3.11+, LangChain BaseChatModel, subprocess, json

---

### Task 1: Create CodexOAuthChatModel

**Objective:** Build a LangChain ChatModel that wraps `codex exec --print`

**Files:**
- Create: `spatialagent/agent/oauth_chatmodels.py`
- Test: `tests/test_oauth_chatmodels.py`

**Step 1: Write failing test**

```python
# tests/test_oauth_chatmodels.py
import unittest
from unittest.mock import patch, MagicMock
from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel

class TestCodexOAuthChatModel(unittest.TestCase):
    def test_llm_type_is_codex_oauth(self):
        model = CodexOAuthChatModel()
        self.assertEqual(model._llm_type, "codex-oauth")

    def test_generate_calls_codex_exec(self):
        model = CodexOAuthChatModel()
        messages = [{"role": "user", "content": "Hello"}]
        
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
            self.assertEqual(result.generations[0][0].text, "Hello from Codex")
```

**Step 2: Run test to verify failure**
```bash
cd ~/SpatialAgent && python3 -m pytest tests/test_oauth_chatmodels.py -v
```
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

```python
# spatialagent/agent/oauth_chatmodels.py
import subprocess
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        
        text = result.stdout.strip() if result.returncode == 0 else f"ERROR: {result.stderr}"
        
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
```

**Step 4: Run test to verify pass**
```bash
cd ~/SpatialAgent && python3 -m pytest tests/test_oauth_chatmodels.py::TestCodexOAuthChatModel -v
```
Expected: 2 PASS

**Step 5: Commit**
```bash
git add spatialagent/agent/oauth_chatmodels.py tests/test_oauth_chatmodels.py
git commit -m "feat: add CodexOAuthChatModel wrapping codex exec"
```

---

### Task 2: Create GeminiOAuthChatModel

**Objective:** Build a LangChain ChatModel wrapping `gemini --prompt`

**Step 1: Write failing test**

```python
# Add to tests/test_oauth_chatmodels.py
class TestGeminiOAuthChatModel(unittest.TestCase):
    def test_llm_type_is_gemini_oauth(self):
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        model = GeminiOAuthChatModel()
        self.assertEqual(model._llm_type, "gemini-oauth")

    def test_generate_calls_gemini_cli(self):
        from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
        model = GeminiOAuthChatModel()
        messages = [{"role": "user", "content": "Hi"}]
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"response": "Hello from Gemini"}'
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = model._generate(messages)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("gemini", args[0])
            self.assertIn("Hello from Gemini", result.generations[0][0].text)
```

**Step 2: Run to verify failure**
```bash
pytest tests/test_oauth_chatmodels.py::TestGeminiOAuthChatModel -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# Add to spatialagent/agent/oauth_chatmodels.py
import json

class GeminiOAuthChatModel(BaseChatModel):
    """LangChain ChatModel wrapping Gemini CLI via Google OAuth."""
    
    model: str = "gemini-3-pro-preview"
    timeout: int = 300
    
    @property
    def _llm_type(self) -> str:
        return "gemini-oauth"
    
    def _generate(self, messages, stop=None, **kwargs):
        prompt = messages[-1].content if messages else ""
        cmd = ["gemini", "--prompt", prompt, "--output-format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                text = data.get("response", result.stdout)
            except json.JSONDecodeError:
                text = result.stdout.strip()
        else:
            text = f"ERROR: {result.stderr}"
        
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
```

**Step 4: Run to verify pass**
```bash
pytest tests/test_oauth_chatmodels.py::TestGeminiOAuthChatModel -v
```
Expected: 2 PASS

**Step 5: Commit**
```bash
git add spatialagent/agent/oauth_chatmodels.py tests/test_oauth_chatmodels.py
git commit -m "feat: add GeminiOAuthChatModel wrapping gemini CLI"
```

---

### Task 3: Register in make_llm.py

**Objective:** Add `codex-oauth` and `gemini-oauth` routing

**Step 1: Write failing test**

```python
# Add to tests/test_oauth_chatmodels.py
class TestMakeLlmOAuthRouting(unittest.TestCase):
    def test_make_llm_codex_oauth_returns_chatmodel(self):
        from spatialagent.agent.make_llm import make_llm
        llm = make_llm("codex-oauth", track_cost=False)
        self.assertEqual(llm._llm_type, "codex-oauth")

    def test_make_llm_gemini_oauth_returns_chatmodel(self):
        from spatialagent.agent.make_llm import make_llm
        llm = make_llm("gemini-oauth", track_cost=False)
        self.assertEqual(llm._llm_type, "gemini-oauth")
```

**Step 2: Run to verify failure**
Expected: FAIL — ValueError "Model 'codex-oauth' not supported"

**Step 3: Write implementation**

```python
# In make_llm.py, BEFORE the "Unknown model" ValueError:
if model == "codex-oauth":
    from spatialagent.agent.oauth_chatmodels import CodexOAuthChatModel
    return CodexOAuthChatModel(callbacks=callbacks, **kwargs)

if model == "gemini-oauth":
    from spatialagent.agent.oauth_chatmodels import GeminiOAuthChatModel
    return GeminiOAuthChatModel(callbacks=callbacks, **kwargs)
```

**Step 4: Run to verify pass**
```bash
pytest tests/test_oauth_chatmodels.py::TestMakeLlmOAuthRouting -v
```
Expected: 2 PASS

**Step 5: Commit**
```bash
git add spatialagent/agent/make_llm.py tests/test_oauth_chatmodels.py
git commit -m "feat: register codex-oauth and gemini-oauth in make_llm"
```

---

### Task 4: Live smoke test + edge cases

**Objective:** Verify both models work end-to-end, handle errors

**Step 1: Edge case tests (timeout, missing CLI)**

```python
class TestOAuthEdgeCases(unittest.TestCase):
    def test_codex_timeout_handled(self):
        model = CodexOAuthChatModel(timeout=1)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("codex", 1)):
            result = model._generate([{"role": "user", "content": "x"}])
            self.assertIn("ERROR", result.generations[0][0].text)

    def test_gemini_not_installed_handled(self):
        model = GeminiOAuthChatModel()
        with patch("subprocess.run", side_effect=FileNotFoundError("gemini")):
            result = model._generate([{"role": "user", "content": "x"}])
            self.assertIn("ERROR", result.generations[0][0].text)
```

**Step 2: Live smoke (manual — requires OAuth session)**

```bash
cd ~/SpatialAgent && python3 -c "
from spatialagent.agent.make_llm import make_llm
llm = make_llm('codex-oauth')
print(llm.invoke('Say OK in one word'))
"
```

**Step 3: Commit final**
```bash
git add -A && git commit -m "test: edge cases for OAuth chat models"
```

---

### Verification

- [ ] All 8 tests pass
- [ ] codex-oauth smoke test returns valid response
- [ ] gemini-oauth smoke test returns valid response  
- [ ] OpenCode Go routing unchanged (verified by existing tests)
- [ ] No regressions in test suite
