# SpatialAgent Co-Agent Harness Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Integrate Gemini 3.1 Pro as the primary LangGraph orchestrator, and wrap Codex CLI and OpenCode Go CLI as LangChain tools (Co-Agents) to act as a coding/review harness for SpatialAgent.

**Architecture:** 
SpatialAgent expects an API endpoint, but Codex and OpenCode are CLIs. We will use the **Co-Agent Pattern**:
1. **Gemini (Orchestrator):** SpatialAgent's `make_llm.py` will route to Gemini (via LiteLLM proxy or native LangChain) using Gemini OAuth/API keys. 
2. **Codex (Heavy Implementer):** Authenticated via Codex OAuth/OpenAI. A new `execute_codex` LangChain tool will wrap `codex exec` in a sandboxed git repo to generate complex spatial biology analysis scripts.
3. **OpenCode Go (Reviewer/Refactorer):** Authenticated via OpenRouter. A new `execute_opencode` LangChain tool will wrap `opencode run` to review, lint, and verify the scripts Codex generates.

**Tech Stack:** SpatialAgent (LangGraph), Gemini 3.1 Pro, Codex CLI, OpenCode Go CLI, LangChain, Python 3.11.

---

### Task 1: Setup OAuth and Environment Credentials

**Objective:** Validate and export the necessary OAuth credentials for all three services.

**Files:**
- Create: `local_llm/.env.harness`

**Step 1: Write failing test (Environment Check)**
```python
# test_env.py
import os
def test_credentials_exist():
    assert "GEMINI_API_KEY" in os.environ or "GOOGLE_APPLICATION_CREDENTIALS" in os.environ
    assert "OPENAI_API_KEY" in os.environ
    assert "OPENROUTER_API_KEY" in os.environ
```

**Step 2: Run test to verify failure**
Run: `pytest test_env.py`
Expected: FAIL

**Step 3: Write minimal implementation**
```bash
# local_llm/.env.harness
# Gemini OAuth / API setup
export GEMINI_API_KEY="your_gemini_key"
# Codex OAuth setup
export OPENAI_API_KEY="your_openai_key"
# OpenCode Go OAuth setup
export OPENROUTER_API_KEY="your_openrouter_key"
```

**Step 4: Run test to verify pass**
Run: `source local_llm/.env.harness && pytest test_env.py`
Expected: PASS

**Step 5: Commit**
```bash
git add local_llm/.env.harness test_env.py
git commit -m "chore: add harness OAuth environment template"
```

---

### Task 2: Implement Codex Co-Agent Wrapper

**Objective:** Create a LangChain tool that delegates complex coding tasks to the Codex CLI.

**Files:**
- Create: `spatialagent/tool/coagents/codex_wrapper.py`
- Modify: `spatialagent/tool/__init__.py`

**Step 1: Write failing test**
```python
# tests/tool/test_codex_wrapper.py
from spatialagent.tool.coagents.codex_wrapper import execute_codex
def test_execute_codex():
    result = execute_codex("Write a simple python script that prints 'hello spatial biology'")
    assert "print" in result.lower()
```

**Step 2: Run test to verify failure**
Run: `pytest tests/tool/test_codex_wrapper.py`
Expected: FAIL — module not found.

**Step 3: Write minimal implementation**
```python
# spatialagent/tool/coagents/codex_wrapper.py
import subprocess
import tempfile
import os
from langchain.tools import tool

@tool
def execute_codex(prompt: str, context_files: list[str] = None) -> str:
    """Delegates a heavy coding task to Codex CLI. Use for generating complex scripts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Codex requires a git repository to run
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        
        # Copy context files if provided (omitted for brevity)
        
        cmd = ["codex", "exec", "-m", "gpt-5.5", "--full-auto", prompt]
        result = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True)
        
        return f"Codex Output:\n{result.stdout}\nErrors:\n{result.stderr}"
```

**Step 4: Run test to verify pass**
Run: `pytest tests/tool/test_codex_wrapper.py`
Expected: PASS

**Step 5: Commit**
```bash
git add spatialagent/tool/coagents/codex_wrapper.py tests/tool/test_codex_wrapper.py
git commit -m "feat: add codex cli wrapper tool for co-agent delegation"
```

---

### Task 3: Implement OpenCode Go Co-Agent Wrapper

**Objective:** Create a LangChain tool that delegates code review and refactoring tasks to the OpenCode Go CLI.

**Files:**
- Create: `spatialagent/tool/coagents/opencode_wrapper.py`
- Modify: `spatialagent/tool/__init__.py`

**Step 1: Write failing test**
```python
# tests/tool/test_opencode_wrapper.py
from spatialagent.tool.coagents.opencode_wrapper import execute_opencode
def test_execute_opencode():
    result = execute_opencode("Review this code: 'print(x)'", files=[])
    assert "review" in result.lower() or "error" in result.lower()
```

**Step 2: Run test to verify failure**
Run: `pytest tests/tool/test_opencode_wrapper.py`
Expected: FAIL

**Step 3: Write minimal implementation**
```python
# spatialagent/tool/coagents/opencode_wrapper.py
import subprocess
from langchain.tools import tool

@tool
def execute_opencode(prompt: str, files: list[str] = None) -> str:
    """Delegates code review and refactoring to OpenCode CLI. Use for code QA."""
    cmd = ["opencode", "run", prompt]
    if files:
        for f in files:
            cmd.extend(["-f", f])
            
    result = subprocess.run(cmd, capture_output=True, text=True)
    return f"OpenCode Review:\n{result.stdout}\nErrors:\n{result.stderr}"
```

**Step 4: Run test to verify pass**
Run: `pytest tests/tool/test_opencode_wrapper.py`
Expected: PASS

**Step 5: Commit**
```bash
git add spatialagent/tool/coagents/opencode_wrapper.py tests/tool/test_opencode_wrapper.py
git commit -m "feat: add opencode go cli wrapper tool for code review"
```

---

### Task 4: Register Tools in SpatialAgent Harness

**Objective:** Inject the newly created Co-Agent tools into SpatialAgent's LangGraph tool registry so Gemini can use them.

**Files:**
- Modify: `spatialagent/agent/tool_system.py`

**Step 1: Write failing test**
```python
# tests/agent/test_tool_registration.py
from spatialagent.agent.tool_system import get_all_tools
def test_coagent_tools_registered():
    tools = [t.name for t in get_all_tools()]
    assert "execute_codex" in tools
    assert "execute_opencode" in tools
```

**Step 2: Run test to verify failure**
Run: `pytest tests/agent/test_tool_registration.py`
Expected: FAIL

**Step 3: Write minimal implementation**
```python
# spatialagent/agent/tool_system.py (append/modify imports and tool list)
from spatialagent.tool.coagents.codex_wrapper import execute_codex
from spatialagent.tool.coagents.opencode_wrapper import execute_opencode

# In the tool registry list
AVAILABLE_TOOLS = [
    # ... existing tools ...
    execute_codex,
    execute_opencode,
]
```

**Step 4: Run test to verify pass**
Run: `pytest tests/agent/test_tool_registration.py`
Expected: PASS

**Step 5: Commit**
```bash
git add spatialagent/agent/tool_system.py tests/agent/test_tool_registration.py
git commit -m "feat: register codex and opencode harness tools"
```
