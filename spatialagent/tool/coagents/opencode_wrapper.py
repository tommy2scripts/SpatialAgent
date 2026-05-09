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
