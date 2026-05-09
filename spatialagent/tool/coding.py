"""
Python REPL and Bash execution tools for CodeAct.

Simple tools that execute code/commands. Paths are configured globally.
"""

import sys
import io
import traceback
import subprocess
import os
import base64
import glob
from contextlib import redirect_stdout, redirect_stderr
from typing import Annotated, Dict, Any, List, Set, Sequence
from langchain_core.tools import tool
from pydantic import Field


# =============================================================================
# Global Configuration
# =============================================================================

_config = {
    "save_path": "./experiments",
    "data_path": "./data",
}

# Store new image files created during execution
_new_image_files: List[str] = []  # List of file paths to new images

def get_new_image_files() -> List[str]:
    """Get and clear list of new image files created during execution."""
    global _new_image_files
    files = _new_image_files.copy()
    _new_image_files = []
    return files

# Tools to inject into REPL namespace (set via inject_tools_into_repl)
_injected_tools = {}

def configure_coding_tools(save_path: str = "./experiments", data_path: str = "./data"):
    """Configure paths for coding tools. Call this before using the tools."""
    _config["save_path"] = save_path
    _config["data_path"] = data_path
    # Reset REPL if paths change
    global _repl_instance
    _repl_instance = None

def inject_tools_into_repl(tools: dict):
    """
    Inject tools into the REPL namespace so they can be called directly.

    Args:
        tools: Dict mapping tool names to callable functions
    """
    global _injected_tools, _repl_instance
    _injected_tools = tools
    # Reset REPL so new tools are available
    _repl_instance = None


# =============================================================================
# Python REPL Implementation
# =============================================================================

class _StatefulPythonREPL:
    """Stateful Python REPL that maintains variables across executions."""

    def __init__(self, save_path: str = None, data_path: str = None):
        self.save_path = save_path or _config["save_path"]
        self.data_path = data_path or _config["data_path"]
        # Use single namespace for both globals and locals
        # This ensures functions defined in exec() can access all variables
        self.namespace = {"__builtins__": __builtins__}
        self._libraries_imported = False

    def _preimport_libraries(self):
        """Lazily import common libraries on first execution."""
        if self._libraries_imported:
            return

        common_imports = f"""
import numpy as np
import pandas as pd
import scanpy as sc
import squidpy as sq
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
import json

import matplotlib
matplotlib.use('Agg')

save_path = r'{self.save_path}'
data_path = r'{self.data_path}'
"""
        try:
            exec(common_imports, self.namespace)
        except Exception as e:
            print(f"Warning: Could not pre-import libraries: {e}")

        # Inject tools into namespace (always, even if library imports fail)
        for tool_name, tool_func in _injected_tools.items():
            self.namespace[tool_name] = tool_func
        self._libraries_imported = True

    def _scan_image_files(self, directory: str) -> Set[str]:
        """Scan directory recursively for image files, return set of (path, mtime) tuples."""
        image_extensions = ('*.png', '*.jpg', '*.jpeg', '*.svg', '*.pdf')
        files = set()
        for ext in image_extensions:
            for f in glob.glob(os.path.join(directory, '**', ext), recursive=True):
                try:
                    mtime = os.path.getmtime(f)
                    files.add((f, mtime))
                except OSError:
                    pass
        return files

    def _find_new_images(self, before: Set[str], after: Set[str]) -> List[str]:
        """Find images that are new or modified."""
        before_paths = {f for f, _ in before}
        new_images = []
        for path, mtime in after:
            if path not in before_paths:
                # Completely new file
                new_images.append(path)
            else:
                # Check if modified (mtime changed)
                old_mtime = next((m for p, m in before if p == path), None)
                if old_mtime and mtime > old_mtime:
                    new_images.append(path)
        return sorted(new_images)  # Sort for consistent ordering

    def _get_monitor_paths(self) -> List[str]:
        """Get list of directories to monitor for new images."""
        paths = set()
        # Always include configured save_path
        paths.add(self.save_path)

        # Common variable names used for output directories
        path_var_names = ['save_path', 'output_dir', 'output_path', 'out_dir', 'fig_dir', 'figure_dir', 'results_dir']

        # Check for these variables in REPL namespace
        for var_name in path_var_names:
            if var_name in self.namespace:
                val = self.namespace[var_name]
                # Handle pathlib.Path objects
                paths.add(str(val))

        # Also check scanpy's figure directory
        try:
            import scanpy as sc
            if hasattr(sc.settings, 'figdir') and sc.settings.figdir:
                paths.add(str(sc.settings.figdir))
        except ImportError:
            pass

        # Filter to existing directories only
        return [p for p in paths if os.path.isdir(p)]

    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code and return results."""
        global _new_image_files
        self._preimport_libraries()

        # Strip markdown code fences if present (LLM sometimes wraps code in ```python ... ```)
        code = code.strip()
        if code.startswith("```"):
            # Remove opening fence (```python, ```py, or just ```)
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove first line
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        # Scan for existing images before execution (in all monitored paths)
        images_before = set()
        for path in self._get_monitor_paths():
            images_before.update(self._scan_image_files(path))

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    result = eval(code, self.namespace)
                    result_str = repr(result) if result is not None else ""
                except SyntaxError:
                    exec(code, self.namespace)
                    result_str = ""

            output = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()

            # Scan for new images after execution (in all monitored paths)
            images_after = set()
            monitor_paths_after = self._get_monitor_paths()
            for path in monitor_paths_after:
                images_after.update(self._scan_image_files(path))
            new_images = self._find_new_images(images_before, images_after)
            _new_image_files.extend(new_images)

            return {
                "success": True,
                "output": output + stderr if stderr else output,
                "result": result_str,
                "error": None
            }

        except Exception as e:
            # Still check for new images even on error
            images_after = set()
            for path in self._get_monitor_paths():
                images_after.update(self._scan_image_files(path))
            new_images = self._find_new_images(images_before, images_after)
            _new_image_files.extend(new_images)

            # Format error clearly for the agent
            tb = traceback.extract_tb(e.__traceback__)
            # Find the line from user code (in <string>)
            user_lines = [frame for frame in tb if frame.filename == "<string>"]

            error_parts = [
                "=" * 60,
                f"ERROR: {type(e).__name__}",
                f"MESSAGE: {str(e)}",
                "=" * 60,
            ]

            if user_lines:
                last_frame = user_lines[-1]
                error_parts.append(f"LINE {last_frame.lineno}: {last_frame.line}")

            error_parts.append("")
            error_parts.append("Fix this error in your next code block.")

            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "result": None,
                "error": "\n".join(error_parts)
            }


# Singleton REPL instance
_repl_instance = None

def _get_repl():
    global _repl_instance
    if _repl_instance is None:
        _repl_instance = _StatefulPythonREPL()
    return _repl_instance


# =============================================================================
# Tools
# =============================================================================

@tool
def execute_python(
    code: Annotated[str, Field(description="Python code to execute")],
) -> str:
    """
    Execute Python code in a stateful environment.

    Pre-imported: numpy (np), pandas (pd), scanpy (sc), squidpy (sq), matplotlib.pyplot (plt), seaborn (sns)
    Available variables: save_path, data_path
    Variables persist across calls.
    """
    repl = _get_repl()
    result = repl.execute(code)

    if result["success"]:
        parts = []
        if result["output"]:
            parts.append(f"Output:\n{result['output']}")
        if result["result"]:
            parts.append(f"Result: {result['result']}")
        if not parts:
            parts.append("Code executed successfully (no output).")
        return "\n\n".join(parts)
    else:
        return f"Error executing code:\n{result['error']}"


@tool
def execute_bash(
    command: Annotated[str, Field(description="Bash command to execute")],
) -> str:
    """
    Execute a Bash shell command.

    Environment variables: $SAVE_PATH, $DATA_PATH
    Default timeout: 60 seconds.
    """
    env = os.environ.copy()
    env['SAVE_PATH'] = _config["save_path"]
    env['DATA_PATH'] = _config["data_path"]

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        if result.returncode == 0:
            parts = []
            if result.stdout:
                parts.append(f"Output:\n{result.stdout}")
            if result.stderr:
                parts.append(f"Warnings:\n{result.stderr}")
            if not parts:
                parts.append("Command executed successfully (no output).")
            return "\n\n".join(parts)
        else:
            return f"Command failed (code {result.returncode}):\n{result.stderr or result.stdout}"

    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds"
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"


# =============================================================================
# External Coding Agent Tools
# =============================================================================

_AGENT_COMMANDS = {
    "claude": lambda task: ["claude", "--print", task],
    "codex": lambda task: [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "-m",
        os.environ.get("CODEX_MODEL", "gpt-5.5"),
        task,
    ],
    "opencode": lambda task: ["opencode", "run", task],
}


def _build_external_agent_command(cli_command: str | Sequence[str], task: str) -> List[str]:
    """Build the subprocess argv for a supported coding-agent CLI."""
    if isinstance(cli_command, str):
        if cli_command in _AGENT_COMMANDS:
            return _AGENT_COMMANDS[cli_command](task)
        return [cli_command, task]

    command = list(cli_command)
    if not command:
        raise ValueError("cli_command cannot be empty")
    return command + [task]


def _run_external_agent(cli_command: str | Sequence[str], task: str, timeout: int = 300) -> Dict[str, Any]:
    """Run an external coding agent CLI and capture output.

    Args:
        cli_command: The CLI command to run (e.g., "claude", "codex") or an argv prefix.
        task: The task/prompt to give the agent
        timeout: Maximum seconds to wait for the agent to complete

    Returns:
        Dict with success, output, error keys
    """
    try:
        timeout = int(timeout)
        if timeout <= 0:
            return {
                "success": False,
                "output": "",
                "error": "timeout must be a positive integer",
            }

        command = _build_external_agent_command(cli_command, task)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "TERM": "dumb"},
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout.strip())
        if result.stderr:
            output_parts.append(f"Stderr:\n{result.stderr.strip()}")

        output = "\n\n".join(output_parts) if output_parts else "(no output)"

        return {
            "success": result.returncode == 0,
            "output": output,
            "error": None if result.returncode == 0 else f"Exit code {result.returncode}",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Agent timed out after {timeout}s",
        }
    except FileNotFoundError:
        command_name = cli_command if isinstance(cli_command, str) else cli_command[0] if cli_command else "agent"
        return {
            "success": False,
            "output": "",
            "error": f"{command_name} not found. Install the CLI and ensure it is on PATH.",
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"{type(e).__name__}: {str(e)}",
        }


def _format_external_agent_result(agent_name: str, result: Dict[str, Any]) -> str:
    """Format co-agent output so failures are visible in <observation> text."""
    if result["success"]:
        return f"{agent_name} completed the task:\n\n{result['output']}"

    output = result.get("output") or "(no output)"
    return (
        f"ERROR: {agent_name} failed: {result['error']}\n\n"
        f"Output:\n{output}\n\n"
        "The co-agent task did not complete. Inspect the error above before retrying."
    )


@tool
def delegate_to_claude_code(
    task: Annotated[str, Field(description="Task description for Claude Code to execute")],
    timeout: Annotated[int, Field(description="Maximum seconds to wait (default: 300)")] = 300,
) -> str:
    """
    Delegate a coding task to Claude Code CLI (Anthropic).

    Claude Code can read/write files, run terminal commands, and reason about codebases.
    Requires 'claude' CLI to be installed: npm install -g @anthropic-ai/claude-code

    Use this for complex tasks that benefit from Claude's code understanding,
    such as refactoring, debugging, or implementing features across multiple files.
    """
    result = _run_external_agent("claude", task, timeout)
    return _format_external_agent_result("Claude Code", result)


@tool
def delegate_to_codex(
    task: Annotated[str, Field(description="Task description for OpenAI Codex to execute")],
    timeout: Annotated[int, Field(description="Maximum seconds to wait (default: 300)")] = 300,
) -> str:
    """
    Delegate a coding task to OpenAI Codex CLI.

    Codex can analyze and modify code, run commands, and solve complex programming tasks.
    Requires 'codex' CLI to be installed: pip install codex-cli

    Use this for tasks that benefit from GPT-5's code reasoning,
    such as algorithm design, code review, or generating test suites.
    """
    result = _run_external_agent("codex", task, timeout)
    return _format_external_agent_result("Codex", result)


@tool
def delegate_to_opencode(
    task: Annotated[str, Field(description="Task description for OpenCode to execute")],
    timeout: Annotated[int, Field(description="Maximum seconds to wait (default: 300)")] = 300,
) -> str:
    """
    Delegate a coding task to OpenCode CLI.

    OpenCode is an open-source coding agent that can read/write files and run commands.
    Requires 'opencode' CLI to be installed.

    Use this for tasks where you want an open-source alternative,
    such as quick scripts, file manipulation, or code exploration.
    """
    result = _run_external_agent("opencode", task, timeout)
    return _format_external_agent_result("OpenCode", result)


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for code that imports StatefulPythonREPL directly
StatefulPythonREPL = _StatefulPythonREPL

def create_python_repl_tool(save_path: str, data_path: str):
    """Deprecated: Use configure_coding_tools() then import execute_python directly."""
    configure_coding_tools(save_path, data_path)
    return execute_python, _get_repl()

def create_bash_tool(save_path: str, data_path: str):
    """Deprecated: Use configure_coding_tools() then import execute_bash directly."""
    configure_coding_tools(save_path, data_path)
    return execute_bash
