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
        
        # We would copy context files here in a full implementation
        
        cmd = ["codex", "exec", "-m", "gpt-5.5", "--full-auto", prompt]
        result = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True)
        
        return f"Codex Output:\n{result.stdout}\nErrors:\n{result.stderr}"
