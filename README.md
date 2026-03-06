# AI-Researcher Fork

A lightweight fork of [HKUDS/AI-Researcher](https://github.com/HKUDS/AI-Researcher) — an autonomous system for end-to-end scientific research automation.

---

## About This Fork

This repository is a personal fork of the original **AI-Researcher** project developed by the [HKUDS Lab](https://github.com/HKUDS) at The University of Hong Kong. The original project was accepted as a **Spotlight paper at NeurIPS 2025**.

### Changes in This Fork

- **Lightweight repository**: Removed large binary datasets, cached evaluation artifacts, and demo media to keep the repo small and fast to clone
- **Provider-aware embeddings**: Default embeddings now use OpenRouter's `qwen/qwen3-embedding-8b` with automatic fallbacks to Ollama or OpenAI
- **Simplified setup**: Streamlined for macOS development with `uv` package manager
- **Bring your own data**: No bundled datasets — point the system at your own data or regenerate artifacts as needed

---

## Original Project

**AI-Researcher** introduces autonomous scientific discovery that automates the entire research lifecycle:

- **Literature Review**: Comprehensive analysis and synthesis of existing research
- **Idea Generation**: Systematic formulation of novel research directions
- **Algorithm Design & Implementation**: Transform ideas into functional code
- **Validation & Refinement**: Automated testing and iterative optimization
- **Result Analysis**: Advanced interpretation of experimental data
- **Manuscript Creation**: Automatic generation of full-length academic papers

The system accepts queries at two levels:
1. **Level 1 (Detailed Ideas)**: Provide comprehensive research descriptions for implementation
2. **Level 2 (Reference-Based)**: Submit reference papers and let the system generate novel ideas

For full details, see the [original project page](https://autoresearcher.github.io) and [documentation](https://autoresearcher.github.io/docs).

---

## Quick Start

### Prerequisites

- Python 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (optional, for sandboxed code execution)
- API keys for your LLM provider (OpenRouter, OpenAI, Anthropic, etc.)

### Installation

```bash
# Clone this fork
git clone https://github.com/alexchaomander/AI-Researcher.git
cd AI-Researcher

# Create virtual environment with uv
uv venv --python 3.11
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# For web GUI support
uv pip install -e ".[full]"

# Install Playwright browsers (for web research tools)
playwright install
```

### Configuration

```bash
# Copy the template
cp .env.template .env

# Edit .env with your settings:
# - OPENROUTER_API_KEY or OPENAI_API_KEY
# - COMPLETION_MODEL (default: openrouter/google/gemini-2.5-pro-preview-05-20)
# - EMBEDDING_MODEL (default: qwen/qwen3-embedding-8b for OpenRouter)
# - GITHUB_AI_TOKEN (for code search)
```

#### Embedding Configuration

The system supports multiple embedding providers with automatic fallbacks:

| Provider | Model | Configuration |
|----------|-------|---------------|
| OpenRouter | `qwen/qwen3-embedding-8b` | Set `OPENROUTER_API_KEY` (default) |
| Ollama | `embeddinggemma:latest` | Set `OLLAMA_BASE_URL=http://localhost:11434` |
| OpenAI | `text-embedding-3-small` | Set `OPENAI_API_KEY` (fallback) |

### Running

```bash
# CLI help
python -m research_agent.inno.cli --help

# Main CLI
ai-researcher --help
ai-researcher run -c vq -i one_layer_vq -l task1
ai-researcher preview -c vq -i one_layer_vq
ai-researcher wizard

# Topic-based workspace (new)
ai-researcher workspace init
ai-researcher workspace create-project --name "Graph Recommendation 2026" --owner alex
ai-researcher workspace create-topic --project graph-recommendation-2026 --title "Cold-start ranking" --owner alex --category-tag recommendation
ai-researcher workspace add-task --project graph-recommendation-2026 --topic cold-start-ranking --task-id literature_discovery --title "Collect latest baselines"
ai-researcher workspace recommend-tasks --project graph-recommendation-2026 --topic cold-start-ranking

# Run metadata and artifacts
ai-researcher metadata --latest --show
ai-researcher bundle --latest
ai-researcher bundle --latest --folder
ai-researcher registry -n 10
ai-researcher clean --apply
ai-researcher bench-validate

# Web GUI (requires .[full] install)
python web_ai_researcher.py

# Run Level 1 task (with detailed idea)
cd research_agent
bash run_infer_level_1.sh

# Run Level 2 task (reference-based ideation)
cd research_agent
bash run_infer_level_2.sh
```

---

## Project Structure

```
AI-Researcher/
├── research_agent/          # Core research automation
│   ├── inno/               # Agent framework (tools, workflows, memory)
│   ├── run_infer_plan.py   # Level 1 task execution
│   ├── run_infer_idea.py   # Level 2 task execution
│   └── constant.py         # Configuration and LLM setup
├── paper_agent/            # Academic paper generation
│   ├── writing.py          # Main orchestrator
│   └── {domain}/           # Domain-specific templates
├── benchmark/
│   ├── final/              # Task definitions (JSON configs)
│   └── process/            # [Lightweight] Artifacts not bundled
├── docker/                 # Containerization support
└── web_ai_researcher.py    # Gradio web interface
```

---

## Docker Setup (Optional)

For sandboxed code execution:

```bash
# Pull the pre-built image
docker pull tjbtech1/airesearcher:v1

# Or build from Dockerfile
cd docker && docker build -t tjbtech1/airesearcher:v1 .
```

Configure GPU access in `.env`:
```bash
GPUS='"device=0"'      # Single GPU
GPUS='"device=0,1"'    # Multiple GPUs
GPUS='"all"'           # All GPUs
GPUS=None              # CPU only
```

---

## Benchmark

Task definitions are available in `benchmark/final/` covering:
- **diffu_flow**: Diffusion flow models
- **gnn**: Graph neural networks
- **reasoning**: Mathematical reasoning
- **recommendation**: Recommendation systems
- **vq**: Vector quantization

This lightweight fork does not bundle the raw datasets or evaluation artifacts. See the [original benchmark documentation](https://autoresearcher.github.io/leaderboard) for full datasets.

---

## Acknowledgements

This fork builds upon the excellent work of the original AI-Researcher team:

- **Original Authors**: Jiabin Tang, Lianghao Xia, Zhonghang Li, Chao Huang
- **Institution**: [HKUDS Lab](https://github.com/HKUDS), The University of Hong Kong
- **Original Repository**: [HKUDS/AI-Researcher](https://github.com/HKUDS/AI-Researcher)
- **Paper**: [arXiv:2505.18705](https://arxiv.org/abs/2505.18705)

---

## Citation

If you use this work, please cite the original paper:

```bibtex
@misc{airesearcher,
    title={{AI-Researcher: Autonomous Scientific Innovation}},
    author={Jiabin Tang and Lianghao Xia and Zhonghang Li and Chao Huang},
    year={2025},
    eprint={2505.18705},
    archivePrefix={arXiv},
    primaryClass={cs.AI},
    url={https://arxiv.org/abs/2505.18705},
}
```

---

## License

This project inherits the license from the original [HKUDS/AI-Researcher](https://github.com/HKUDS/AI-Researcher) repository. See the original repo for license details.

---

## Links

- [Original Project Page](https://autoresearcher.github.io)
- [Original Documentation](https://autoresearcher.github.io/docs)
- [Original GitHub](https://github.com/HKUDS/AI-Researcher)
- [Paper on arXiv](https://arxiv.org/abs/2505.18705)
- [Benchmark Leaderboard](https://autoresearcher.github.io/leaderboard)
