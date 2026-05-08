## SpatialAgent

This is the official implementation for **SpatialAgent: An autonomous AI agent for spatial biology**.

Contact wang.hanchen@gene.com or hanchenw@stanford.edu if you have any questions.

![teaser](teaser.png)

### Overview

SpatialAgent is an autonomous AI agent for spatial transcriptomics, single-cell RNA-seq, and molecular biology. It integrates large language models with dynamic tool execution and adaptive reasoning, spanning the entire research workflow from experimental design to multimodal data analysis and hypothesis generation.

Key features:
- **Plan-Act-Conclude architecture** with direct code execution
- **72 specialized tools** for database queries, literature mining, spatial analytics, and genomic analysis
- **17 skill templates** for guided workflows (annotation, CCI, panel design, spatial mapping, etc.)
- **Multi-model support**: Claude, GPT, Gemini, Bedrock, OpenRouter, z.AI, and local models

### Installation

```bash
# Setup environment
./setup_env.sh              # Creates 'spatial_agent' environment, python 3.11
conda activate spatial_agent

# Set API keys (pick your provider)
export ANTHROPIC_API_KEY=your_key    # For Claude models
export OPENAI_API_KEY=your_key       # For GPT models
export GOOGLE_API_KEY=your_key       # For Gemini models (optional)
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
```

### Model Configuration

SpatialAgent supports multiple model providers through a unified `make_llm()` interface.

#### Cloud API Models

```python
# Anthropic Claude (via direct API)
make_llm("claude-sonnet-4-5-20250929")
make_llm("claude-opus-4-5-20251101")
make_llm("claude-haiku-4-5-20251001")

# OpenAI (direct)
make_llm("gpt-5")
make_llm("gpt-5-pro")

# Google Gemini
make_llm("gemini-3-pro-preview")

# AWS Bedrock (Claude via AWS)
make_llm("us.anthropic.claude-sonnet-4-5-20250929-v1:0")
```

#### OpenRouter Models

Prefix the model name with `openrouter/`:

```bash
# Set OpenRouter key
export OPENROUTER_API_KEY=your_key
```

```python
make_llm("openrouter/anthropic/claude-sonnet-4")
make_llm("openrouter/google/gemini-2.5-pro")
make_llm("openrouter/deepseek/deepseek-v4")
```

Optional env vars:
- `OPENROUTER_BASE_URL` — custom endpoint (default: https://openrouter.ai/api/v1)
- `OPENROUTER_HTTP_REFERER` — for analytics/referrer tracking
- `OPENROUTER_APP_TITLE` — app title sent with requests

#### z.AI Models

Prefix the model name with `zai/`:

```bash
# Set z.AI key
export ZAI_API_KEY=your_key
```

```python
make_llm("zai/qwen3-72b")
make_llm("zai/deepseek-v3")
```

Optional env var: `ZAI_BASE_URL` (default: https://api.z.ai/api/paas/v4)

#### Local Models

Prefix the model name with `local/`:

```bash
export LOCAL_LLM_BASE_URL=http://localhost:11434/v1   # Ollama
# or
export LOCAL_LLM_BASE_URL=http://localhost:8080/v1     # LiteLLM proxy
```

```python
make_llm("local/llama3.2")
make_llm("local/qwen3-vl-32b")
```

#### Generic OpenAI-Compatible Endpoints

Set env vars directly for any OpenAI-compatible endpoint:

```bash
export CUSTOM_LLM_BASE_URL=http://localhost:8080/v1
export CUSTOM_LLM_API_KEY=your_key    # or "EMPTY" for local
```

```python
make_llm("qwen3-vl-32b")  # routes through CUSTOM_LLM_BASE_URL
```

Env var cascade (first found wins): `CUSTOM_LLM_BASE_URL` > `CUSTOM_MODEL_BASE_URL` > `OPENAI_BASE_URL`

### Local LLM Serving

SpatialAgent can run entirely with locally-served LLMs — no API keys required.

#### Prerequisites

- **NVIDIA GPUs** (vLLM backend) or **Apple Silicon Mac** (MLX backend)

#### Linux + NVIDIA (vLLM)

```bash
./local_llm/vllm/setup.sh                # One-time setup (creates .venv-vllm, .venv-litellm)

./local_llm/vllm/start.sh                # Start with Qwen3-VL-32B (default)
./local_llm/vllm/start.sh ministral      # Or start with Ministral-3-14B
./local_llm/vllm/start.sh status         # Check server status
./local_llm/vllm/start.sh stop           # Stop all servers
```

#### macOS + Apple Silicon (MLX)

```bash
./local_llm/mlx/setup.sh                 # One-time setup (creates .venv-mlx)

./local_llm/mlx/start.sh                 # Start servers
./local_llm/mlx/start.sh status          # Check server status
./local_llm/mlx/start.sh stop            # Stop all servers
```

After starting the servers:

```bash
# Point SpatialAgent to local servers via LiteLLM proxy
export CUSTOM_MODEL_BASE_URL=http://localhost:8080/v1
export CUSTOM_EMBED_BASE_URL=http://localhost:8080/v1
export CUSTOM_EMBED_MODEL=qwen3-embedding
export TOKENIZERS_PARALLELISM=false
```

Then use as usual:

```python
llm = make_llm("qwen3-vl-32b")
agent = SpatialAgent(llm=llm, save_path="./experiments/local/")
```

See [`docs/local_llm_setup.md`](docs/local_llm_setup.md) for full configuration details.

### Supported Models

| Model | Method | Description |
|-------|--------|-------------|
| Claude Sonnet/Opus/Haiku | `claude-*` | Anthropic's Claude family (direct API) |
| GPT-5 / GPT-5 Pro | `gpt-5*` | OpenAI GPT models |
| Gemini 3 Pro/Flash | `gemini-*` | Google Gemini models |
| Bedrock Claude | `us.anthropic.claude-*` | Claude via AWS Bedrock |
| OpenRouter models | `openrouter/<model>` | Any OpenRouter model |
| z.AI models | `zai/<model>` | Any z.AI model |
| Local models | `local/<model>` | Any OpenAI-compatible local endpoint |
| Custom endpoints | via `CUSTOM_LLM_BASE_URL` | LiteLLM, vLLM, Ollama, etc. |
| Qwen3-VL-32B | vLLM | Vision-language model (local, default) |
| Ministral-3-14B | vLLM | Mistral's lightweight model (local) |
| MLX models | MLX | Apple Silicon optimized (local) |

### Project Structure

```
SpatialAgent/
├── local_llm/
│   ├── vllm/              # vLLM server scripts (Linux + NVIDIA)
│   ├── mlx/               # MLX server scripts (macOS + Apple Silicon)
│   └── shared/            # Shared configs (custom callbacks)
├── spatialagent/
│   ├── agent/             # Agent implementation
│   ├── skill/             # Skill templates (17 guided workflows)
│   ├── tool/              # Tool implementations (72 tools)
│   └── hooks.py           # Event hooks
├── benchmarks/            # Local model benchmark scripts
├── evaluation/            # Evaluation modules
├── data/                  # Reference databases (CellMarker, PanglaoDB, CZI catalog)
├── docs/                  # Documentation
├── main.ipynb             # Quick start notebook
└── setup_env.sh           # Environment setup
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
