<div align="center">

# D.E.E.P.A.K.

### Distributed Environment for Extrapolating Probability and Artificial Knowledge

---

**A Universal Swarm Intelligence Engine powered by Claude,**
**that builds parallel digital worlds and extrapolates the future.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg?style=flat-square)](LICENSE)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude-cc785c?style=flat-square&logo=anthropic&logoColor=white)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)]()
[![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)]()

</div>

---

## What is D.E.E.P.A.K.?

**D.E.E.P.A.K.** is an AI-powered prediction engine built on swarm intelligence and **Anthropic's Claude** models. Feed it any seed material — breaking news, policy drafts, financial signals, research papers, or even fiction — and it constructs a high-fidelity parallel digital world populated by thousands of Claude-powered autonomous agents, each with their own personality, memory, and behavioral logic.

These agents interact freely, forming emergent social dynamics. You observe from a god's-eye view, inject variables in real-time, and watch the future unfold in a digital sandbox.

> **Input:** Upload seed material + describe your prediction in natural language
>
> **Output:** A comprehensive prediction report + a fully interactive digital world you can explore

---

## Why Claude?

D.E.E.P.A.K. is built exclusively on **Anthropic's Claude** models because swarm intelligence demands agents that can truly reason:

| Claude Capability | How D.E.E.P.A.K. Uses It |
|-------------------|--------------------------|
| **Deep Reasoning** | Agents reason about complex social dynamics, not just pattern-match |
| **Long Context** | Agents maintain rich memories across simulation rounds |
| **Structured Output** | Reliable JSON generation for ontologies, configs, and profiles |
| **Tool Use** | Report Agent uses ReACT pattern with graph search tools |
| **Safety** | Built-in guardrails for responsible autonomous agent behavior |

### Supported Claude Models

| Model | Env Value | Best For |
|-------|-----------|----------|
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | Balanced speed + intelligence (recommended) |
| **Claude Opus 4** | `claude-opus-4-20250514` | Maximum intelligence for complex simulations |
| **Claude Haiku 4.5** | `claude-haiku-4-5-20251001` | Fastest, most cost-effective for large swarms |

---

## Architecture

```
D.E.E.P.A.K./
├── AGENT/                              # Swarm Intelligence Agents (Claude-powered)
│   ├── ontology_generator/             # Designs domain ontologies from text
│   ├── simulation_config_generator/    # Generates simulation parameters
│   ├── report_agent/                   # ReACT agent with tool use for analysis
│   └── oasis_profile_generator/        # Creates autonomous agent personas
│
├── backend/                            # Flask API Server
│   ├── app/
│   │   ├── api/                        # REST endpoints (graph, simulation, report)
│   │   ├── models/                     # Data models (project, task)
│   │   ├── services/                   # Infrastructure & utilities
│   │   │   ├── graph_builder.py        # Knowledge graph construction
│   │   │   ├── simulation_runner.py    # Simulation process orchestrator
│   │   │   ├── simulation_manager.py   # Lifecycle & state management
│   │   │   ├── simulation_ipc.py       # Inter-process communication
│   │   │   ├── text_processor.py       # Document chunking & processing
│   │   │   ├── zep_entity_reader.py    # Knowledge graph data access
│   │   │   ├── zep_graph_memory_updater.py  # Memory synchronization
│   │   │   └── zep_tools.py            # Graph search & retrieval tools
│   │   ├── utils/
│   │   │   ├── llm_client.py           # Anthropic Claude SDK client
│   │   │   ├── logger.py               # Logging utilities
│   │   │   └── retry.py                # Retry logic
│   │   └── config.py                   # Configuration management
│   ├── scripts/                        # Simulation execution scripts
│   └── run.py                          # Backend entry point
│
├── frontend/                           # Vue 3 + Vite SPA
│   └── src/
│       ├── components/                 # Step-by-step workflow UI
│       ├── views/                      # Page views
│       └── api/                        # API client layer
│
├── Dockerfile                          # Container build
├── docker-compose.yml                  # One-command deployment
└── .env.example                        # Environment template
```

---

## Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. GRAPH BUILD  │────▶│  2. ENV SETUP    │────▶│  3. SIMULATE     │
│                 │     │                 │     │                 │
│ Upload seed     │     │ Claude designs  │     │ Claude-powered  │
│ material        │     │ domain ontology │     │ agents interact │
│ Build knowledge │     │ Generates agent │     │ across platforms│
│ graph (GraphRAG)│     │ personas & config│    │ Dynamic memory  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│  5. INTERACT     │◀────│  4. REPORT       │◀─────────────┘
│                 │     │                 │
│ Chat with any   │     │ Claude ReACT    │
│ agent in the    │     │ agent analyzes  │
│ simulated world │     │ with tool use   │
└─────────────────┘     └─────────────────┘
```

1. **Graph Build** — Upload documents. D.E.E.P.A.K. extracts entities, relationships, and injects them into a knowledge graph via Zep + GraphRAG.
2. **Environment Setup** — Claude designs the domain ontology, creates detailed agent personas with unique personalities, and generates simulation parameters.
3. **Simulation** — Thousands of Claude-powered agents run in parallel across Twitter/Reddit environments, posting, reacting, following, and debating autonomously.
4. **Report Generation** — The Report Agent (Claude with ReACT loop) plans investigations, calls graph search tools, and produces a deep analysis report.
5. **Interactive Exploration** — Chat directly with any Claude-powered agent in the post-simulation world, or query the Report Agent for further insights.

---

## Quick Start

### Prerequisites

| Tool | Version | Purpose | Check |
|------|---------|---------|-------|
| **Node.js** | 18+ | Frontend runtime | `node -v` |
| **Python** | 3.11 – 3.12 | Backend runtime | `python --version` |
| **uv** | latest | Python package manager | `uv --version` |
| **Anthropic API Key** | — | Claude access | [console.anthropic.com](https://console.anthropic.com/) |

### 1. Clone & Configure

```bash
git clone https://github.com/DeepakGhengat/D.E.E.P.A.K.-Distributed-Environment-for-Extrapolating-Probability-and-Artificial-Knowledge..git
cd D.E.E.P.A.K.-Distributed-Environment-for-Extrapolating-Probability-and-Artificial-Knowledge.

# Copy environment template
cp .env.example .env
```

Edit `.env` with your keys:

```env
# Anthropic Claude API Key
# Get yours at https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...

# Claude model (see model options below)
CLAUDE_MODEL_NAME=claude-sonnet-4-20250514

# Zep Cloud (knowledge graph memory)
# Free tier at https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key
```

#### Choosing a Claude Model

| Model | Speed | Intelligence | Cost | Use Case |
|-------|-------|-------------|------|----------|
| `claude-sonnet-4-20250514` | Fast | High | Medium | Default — best balance for most simulations |
| `claude-opus-4-20250514` | Moderate | Highest | Higher | Complex scenarios needing maximum reasoning |
| `claude-haiku-4-5-20251001` | Fastest | Good | Lowest | Large swarms, rapid prototyping, cost-sensitive |

### 2. Install Dependencies

```bash
# Install everything (Node.js + Python) in one command
npm run setup:all
```

Or step by step:

```bash
npm run setup           # Node.js dependencies (root + frontend)
npm run setup:backend   # Python dependencies (auto-creates virtualenv via uv)
```

### 3. Run

```bash
# Start both frontend and backend simultaneously
npm run dev
```

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:5001 |

Start individually:

```bash
npm run backend    # Backend only (Flask + Claude)
npm run frontend   # Frontend only (Vue + Vite)
```

---

## Docker Deployment

```bash
# Configure environment
cp .env.example .env
# Edit .env with your Anthropic API key and Zep key

# Build and run
docker compose up -d
```

Ports `3000` (frontend) and `5001` (backend) are exposed by default.

---

## Swarm Agents (AGENT/)

All agents in the `AGENT/` directory are powered by Claude:

| Agent | Claude Does |
|-------|-------------|
| **Ontology Generator** | Analyzes uploaded documents and uses Claude's reasoning to design entity types, relationship structures, and domain-specific ontologies |
| **Simulation Config Generator** | Claude reasons about time zones, activity patterns, event schedules and generates optimal simulation parameters |
| **Report Agent** | Claude runs a multi-step ReACT loop — plans what to investigate, calls graph search tools, interviews entities, reflects, and writes comprehensive reports |
| **OASIS Profile Generator** | Claude creates rich agent personas with distinct personalities, memories, behavioral traits, and platform-specific profiles |

---

## How Claude API is Used

D.E.E.P.A.K. integrates the Anthropic Claude API at two levels:

### 1. Direct Anthropic SDK (`anthropic` Python package)

Used by the core AGENT modules and backend LLM client for:
- **Ontology generation** — Claude analyzes documents and designs domain ontologies
- **Profile generation** — Claude creates detailed agent personas with unique personalities
- **Simulation config** — Claude reasons about optimal simulation parameters
- **Report generation** — Claude runs multi-step ReACT investigations with tool use
- **All backend LLM calls** — The unified `LLMClient` class wraps `anthropic.Anthropic`

```python
# How D.E.E.P.A.K. calls Claude (backend/app/utils/llm_client.py)
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system="You are a domain ontology expert...",
    messages=[{"role": "user", "content": "Analyze this document..."}],
    max_tokens=4096,
    temperature=0.7,
)
```

### 2. CAMEL-AI Framework (native Anthropic support)

The OASIS simulation engine runs on [CAMEL-AI](https://github.com/camel-ai/camel), which has **native `ModelPlatformType.ANTHROPIC` support**. Simulation agents use Claude directly through CAMEL's model factory:

```python
# How simulations use Claude (backend/scripts/)
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from camel.configs import AnthropicConfig

model = ModelFactory.create(
    model_platform=ModelPlatformType.ANTHROPIC,
    model_type="claude-sonnet-4-20250514",
    model_config_dict=AnthropicConfig().as_dict(),
)
```

### API Key Flow

```
.env (ANTHROPIC_API_KEY)
    │
    ├── backend/app/config.py ──► LLMClient (anthropic SDK)
    │                                ├── Ontology Generator Agent
    │                                ├── Simulation Config Agent
    │                                ├── Report Agent (ReACT)
    │                                └── Profile Generator Agent
    │
    └── backend/scripts/ ──► CAMEL ModelFactory (ModelPlatformType.ANTHROPIC)
                                 ├── Twitter Simulation Agents
                                 ├── Reddit Simulation Agents
                                 └── Parallel Simulation Agents
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key from [console.anthropic.com](https://console.anthropic.com/) |
| `CLAUDE_MODEL_NAME` | No | Claude model to use (default: `claude-sonnet-4-20250514`) |
| `ZEP_API_KEY` | Yes | Zep Cloud API key for knowledge graph memory |
| `ANTHROPIC_BOOST_API_KEY` | No | Secondary Anthropic key for parallel simulation throughput |
| `CLAUDE_BOOST_MODEL_NAME` | No | Model for boost config (e.g., `claude-haiku-4-5-20251001` for speed) |

---

## Tech Stack

- **AI Engine:** Anthropic Claude (Sonnet 4 / Opus 4 / Haiku 4.5) via `anthropic` Python SDK
- **Simulation:** CAMEL-AI + OASIS with native `ModelPlatformType.ANTHROPIC` integration
- **Backend:** Python 3.11+ / Flask / Zep Cloud
- **Frontend:** Vue 3 / Vite / D3.js (graph visualization) / Axios
- **Infrastructure:** Docker / uv (Python) / npm (Node.js)

---

## Getting Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys** in the dashboard
4. Click **Create Key** and copy the key (starts with `sk-ant-`)
5. Paste it into your `.env` file as `ANTHROPIC_API_KEY=sk-ant-...`

Claude API pricing is pay-per-token. For typical simulations:
- **Haiku 4.5** — most cost-effective for large agent swarms
- **Sonnet 4** — recommended default, balances quality and cost
- **Opus 4** — maximum reasoning power for complex scenarios

---

## Acknowledgments

- AI powered by [Anthropic Claude](https://anthropic.com)
- Simulation engine powered by [OASIS](https://github.com/camel-ai/oasis) from CAMEL-AI

---

## License

[GNU Affero General Public License v3.0](LICENSE)
