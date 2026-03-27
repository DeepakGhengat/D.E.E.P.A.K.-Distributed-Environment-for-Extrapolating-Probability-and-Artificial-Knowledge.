<div align="center">

# D.E.E.P.A.K.

### Distributed Environment for Extrapolating Probability and Artificial Knowledge

---

**A Universal Swarm Intelligence Engine that builds parallel digital worlds,**
**runs thousands of autonomous agents, and extrapolates the future.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)]()
[![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)]()
[![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=flat-square&logo=flask&logoColor=white)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)]()

</div>

---

## What is D.E.E.P.A.K.?

**D.E.E.P.A.K.** is an AI-powered prediction engine built on swarm intelligence. Feed it any seed material — breaking news, policy drafts, financial signals, research papers, or even fiction — and it constructs a high-fidelity parallel digital world populated by thousands of autonomous agents, each with their own personality, memory, and behavioral logic.

These agents interact freely, forming emergent social dynamics. You observe from a god's-eye view, inject variables in real-time, and watch the future unfold in a digital sandbox.

> **Input:** Upload seed material (reports, articles, stories) + describe your prediction in natural language
>
> **Output:** A comprehensive prediction report + a fully interactive digital world you can explore

---

## Why D.E.E.P.A.K.?

Traditional prediction models treat the world as equations. D.E.E.P.A.K. treats it as what it actually is — **a complex system of interacting individuals whose collective behavior emerges from the bottom up**.

| Capability | Description |
|-----------|-------------|
| **Swarm Emergence** | Thousands of agents with individual personalities produce collective patterns no single model could predict |
| **Knowledge Graphs** | Automatic entity extraction and relationship mapping via GraphRAG |
| **Dual-Platform Simulation** | Parallel social simulation across Twitter and Reddit environments |
| **Autonomous Agents** | LLM-powered agents that reason, plan, and act independently |
| **ReACT Reporting** | Multi-step reasoning agent that investigates simulation results with tools |
| **Interactive Exploration** | Chat with any agent in the simulated world post-simulation |

---

## Architecture

```
D.E.E.P.A.K./
├── AGENT/                              # Swarm Intelligence Agents (LLM-powered)
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
│   │   ├── utils/                      # LLM client, logging, retry logic
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
│ Upload seed     │     │ Extract entities │     │ Dual-platform   │
│ material        │     │ Generate agent   │     │ parallel sim    │
│ Build knowledge │     │ personas         │     │ Dynamic memory  │
│ graph (GraphRAG)│     │ Configure params │     │ updates         │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│  5. INTERACT     │◀────│  4. REPORT       │◀─────────────┘
│                 │     │                 │
│ Chat with any   │     │ ReACT agent     │
│ agent in the    │     │ investigates    │
│ simulated world │     │ with tool use   │
└─────────────────┘     └─────────────────┘
```

1. **Graph Build** — Upload documents. D.E.E.P.A.K. extracts entities, relationships, and injects them into a knowledge graph via Zep + GraphRAG.
2. **Environment Setup** — The Ontology Generator agent designs the domain structure. The Profile Generator agent creates detailed personas. The Config Generator agent determines simulation parameters.
3. **Simulation** — Thousands of agents run in parallel across Twitter/Reddit environments, posting, reacting, following, and debating autonomously.
4. **Report Generation** — The Report Agent uses a ReACT loop (Reason → Act → Observe) with graph search tools to produce a deep analysis.
5. **Interactive Exploration** — Chat directly with any agent in the post-simulation world, or query the Report Agent for further insights.

---

## Quick Start

### Prerequisites

| Tool | Version | Purpose | Check |
|------|---------|---------|-------|
| **Node.js** | 18+ | Frontend runtime | `node -v` |
| **Python** | 3.11 – 3.12 | Backend runtime | `python --version` |
| **uv** | latest | Python package manager | `uv --version` |

### 1. Clone & Configure

```bash
git clone https://github.com/DeepakGhengat/D.E.E.P.A.K.-Distributed-Environment-for-Extrapolating-Probability-and-Artificial-Knowledge..git
cd D.E.E.P.A.K.-Distributed-Environment-for-Extrapolating-Probability-and-Artificial-Knowledge.

# Copy environment template
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# LLM Configuration (any OpenAI-compatible API)
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Zep Cloud (knowledge graph memory)
# Free tier available at https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key

# Optional: Boost LLM (separate faster model for high-throughput tasks)
# LLM_BOOST_API_KEY=your_boost_key
# LLM_BOOST_BASE_URL=your_boost_url
# LLM_BOOST_MODEL_NAME=your_boost_model
```

### 2. Install Dependencies

```bash
# Install everything (Node.js + Python) in one command
npm run setup:all
```

Or step by step:

```bash
npm run setup           # Node.js dependencies (root + frontend)
npm run setup:backend   # Python dependencies (auto-creates virtualenv)
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
npm run backend    # Backend only
npm run frontend   # Frontend only
```

---

## Docker Deployment

```bash
# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Build and run
docker compose up -d
```

Ports `3000` (frontend) and `5001` (backend) are exposed by default.

---

## Swarm Agents (AGENT/)

The `AGENT/` directory contains only LLM-powered autonomous reasoning agents:

| Agent | What It Does |
|-------|-------------|
| **Ontology Generator** | Analyzes documents via LLM to design domain-specific entity types and relationship structures |
| **Simulation Config Generator** | Reasons about simulation requirements to generate time configs, activity patterns, and event schedules |
| **Report Agent** | Multi-step ReACT agent that plans investigations, calls graph search tools, interviews entities, and produces comprehensive reports |
| **OASIS Profile Generator** | Creates detailed agent personas with personalities, memories, and behavioral traits using LLM reasoning |

All non-agent code (graph builders, simulation runners, IPC, memory updaters) lives in `backend/app/services/`.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | API key for your LLM provider |
| `LLM_BASE_URL` | Yes | Base URL (OpenAI-compatible format) |
| `LLM_MODEL_NAME` | Yes | Model name (e.g., `gpt-4o-mini`, `qwen-plus`) |
| `ZEP_API_KEY` | Yes | Zep Cloud API key for knowledge graph memory |
| `LLM_BOOST_API_KEY` | No | Optional separate key for high-throughput LLM tasks |
| `LLM_BOOST_BASE_URL` | No | Optional boost model base URL |
| `LLM_BOOST_MODEL_NAME` | No | Optional boost model name |

---

## Tech Stack

- **Backend:** Python 3.11+ / Flask / Zep Cloud / OASIS simulation engine
- **Frontend:** Vue 3 / Vite / D3.js (graph visualization) / Axios
- **AI:** Any OpenAI-compatible LLM API / GraphRAG / ReACT pattern
- **Infrastructure:** Docker / uv (Python) / npm (Node.js)

---

## Acknowledgments

Simulation engine powered by [OASIS](https://github.com/camel-ai/oasis) from the CAMEL-AI team.

---

## License

[GNU Affero General Public License v3.0](LICENSE)
