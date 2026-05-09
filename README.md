## SpatialAgent

This is the official implementation for **SpatialAgent: An autonomous AI agent for spatial biology**.

Contact wang.hanchen@gene.com or hanchenw@stanford.edu if you have any questions.

![teaser](teaser.png)

### Overview

SpatialAgent is an autonomous AI agent for spatial transcriptomics, single-cell RNA-seq, and molecular biology. It integrates large language models with dynamic tool execution and adaptive reasoning, spanning the entire research workflow from experimental design to multimodal data analysis and hypothesis generation.

Key features:
- **Plan-Act-Conclude architecture** with direct code execution
- **72+ specialized tools** for database queries, literature mining, spatial analytics, and genomic analysis
- **17 skill templates** for guided workflows (annotation, CCI, panel design, spatial mapping, etc.)
- **Multi-model support**: Claude, GPT, Gemini, OpenRouter, z.AI, and local OpenAI-compatible model gateways
- **External coding agents**: Delegate complex tasks to Claude Code, Codex CLI, or OpenCode CLI

### Installation

```bash
# Setup environment
./setup_env.sh              # Creates 'spatial_agent' environment, python 3.11
conda activate spatial_agent

# Set API keys
export ANTHROPIC_API_KEY=your_key    # For Claude models
export OPENAI_API_KEY=your_key       # For GPT models
export GEMINI_API_KEY=your_key       # For Gemini models (optional)

# Optional: OpenAI-compatible providers
export OPENROUTER_API_KEY=your_key   # OpenRouter
export ZAI_API_KEY=your_key          # z.AI
export OPENCODE_GO_API_KEY=your_key  # OpenCode Go endpoint
export LOCAL_LLM_BASE_URL=http://localhost:11434/v1  # Local gateway (Ollama/vLLM/LM Studio)
```

### Quick Start

See `main.ipynb` for a quick overview.

```python
from spatialagent.agent import SpatialAgent, make_llm

llm = make_llm("claude-sonnet-4-5-20250929")
agent = SpatialAgent(llm=llm, save_path="./experiments/demo/")

result = agent.run(
    "Find mouse brain cortex datasets from CZI and analyze neuronal cell types",
    config={"thread_id": "analysis_1"}
)

# Use OpenRouter
llm = make_llm("openrouter/openai/gpt-4o-mini")

# Use z.AI
llm = make_llm("zai/glm-4.6")

# Use OpenCode Go (bare prefix defaults to a non-reasoning model)
llm = make_llm("opencode-go")

# Use a specific OpenCode Go model
llm = make_llm("opencode-go/kimi-k2.6")

# Reasoning-content models get a larger default max_tokens budget
llm = make_llm("opencode-go/deepseek-v4-flash")

# Use local model gateway
llm = make_llm("local/qwen2.5:14b")
```

### OpenCode Go Notes

OpenCode Go is routed through the OpenAI-compatible endpoint at `https://opencode.ai/zen/go/v1`.

```bash
export OPENCODE_GO_API_KEY=your_key
# Optional overrides
export OPENCODE_GO_BASE_URL=https://opencode.ai/zen/go/v1
export OPENCODE_GO_MODEL=kimi-k2.6
export SPATIALAGENT_REASONING_MAX_TOKENS=32768
```

Use `make_llm("opencode-go")` for the default non-reasoning model. Use explicit models such as `make_llm("opencode-go/kimi-k2.6")`, `make_llm("opencode-go/qwen3.6-plus")`, or `make_llm("opencode-go/deepseek-v4-flash")` when you want a particular backend. `deepseek-v4-flash` can emit `reasoning_content` before final content, so SpatialAgent automatically raises its default completion budget unless you pass `max_tokens` yourself.

### Co-Agent Pattern

SpatialAgent can delegate coding work from inside an `<act>` block. The co-agent tools are loaded like normal tools and can be called from the Python REPL namespace when selected:

```python
delegate_to_codex(
    task="Review spatialagent/agent/make_llm.py for routing bugs and suggest a patch",
    timeout=300,
)

delegate_to_opencode(
    task="Review this analysis script for file I/O and plotting issues",
    timeout=300,
)
```

Install the corresponding CLIs first (`codex` for Codex CLI, `opencode` for OpenCode CLI). If a CLI is missing, times out, or exits non-zero, the tool returns an `ERROR:` observation so the LangGraph loop can inspect the failure and retry or conclude with the visible error.

### Project Structure

```
SpatialAgent/
├── spatialagent/
│   ├── agent/              # Agent implementation
│   ├── skill/              # Skill templates (17 guided workflows)
│   ├── tool/               # Tool implementations (72 tools)
│   └── hooks.py            # Event hooks
├── data/                   # Reference databases (CellMarker, PanglaoDB, CZI catalog)
├── resource/               # Dependencies and external packages
├── notebooks/              # Example notebooks
├── docs/                   # Documentation
├── main.ipynb              # Quick start notebook
└── setup_env.sh            # Environment setup
```

### Citation

```bibtex
@article{spatialagent,
	author = {Hanchen Wang and Yichun He and Coelho Paula and Matthew Bucci and Abbas Nazir and other},
	title = {SpatialAgent: An autonomous AI agent for spatial biology},
	doi = {10.1101/2025.04.01.646459},
	publisher = {Cold Spring Harbor Laboratory},
	URL = {https://www.biorxiv.org/content/early/2025/04/01/2024.04.01.646459},
	journal = {bioRxiv},
	year = {2025},
}
```

### License

MIT License. See [LICENSE.txt](LICENSE.txt).
