# AI Receptionist - Technology Stack

## Core Framework

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Runtime** | Python 3.12+ | Modern, async support, LLM library ecosystem |
| **Agentic Framework** | Agno SDK | Model-agnostic, native tool calling, SQLite integration, FastAPI via AgentOS |
| **Database** | SQLite | Simple, file-based, Agno native support via `SqliteDb` |
| **API Framework** | FastAPI | Integrated via Agno's `AgentOS`, async, auto-docs |

---

## AI/LLM

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Primary LLM** | OpenAI GPT-4o-mini | Best function calling, cost-effective |
| **Model Routing** | LiteLLM (optional) | Future flexibility for multi-provider support |

---

## Frontend

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Chat Widget (v1)** | Vanilla JS/HTML/CSS | Simple, embeddable, no build step |
| **Chat Widget (v2+)** | React | Rich UI components (calendar picker) |
| **Admin Panel** | React + Tailwind CSS | Modern, responsive admin interface |

---

## Web Scraping

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **HTTP Client** | httpx | Modern async client, HTTP/2 support |
| **HTML Parser** | BeautifulSoup4 | Simple CSS selector parsing |

**Why not Scrapy?** Overkill for 1-5 pages per business; Scrapy is designed for large-scale crawling with pipelines, spiders, and complex scheduling. For simple single-page extraction, httpx + BeautifulSoup is lighter and more maintainable.

---

## Data Storage

| Data Type | Storage |
|-----------|---------|
| Business configs | SQLite (structured) |
| Users/Auth | SQLite |
| Conversations | SQLite (Agno memory) |
| Appointments | SQLite |
| Leads | SQLite |
| Service templates | YAML files (per vertical) |
| Scraped raw content | SQLite (fallback reference) |

---

## Authentication

- Simple username + role (admin/business_owner)
- No password for MVP
- Session-based with SQLite storage

---

## Package Management

| Tool | Use |
|------|-----|
| **uv** | Python package manager and runner |
| **pnpm** | Frontend package management |

---

## Key Dependencies

```
agno>=1.0.0
fastapi
uvicorn
httpx
beautifulsoup4
lxml
pydantic
openai
pyyaml
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend Layer                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐    │
│  │  Chat Widget    │    │       Admin Panel (React)       │    │
│  │  (Vanilla JS)   │    │       + Tailwind CSS            │    │
│  └────────┬────────┘    └──────────────┬──────────────────┘    │
└───────────┼─────────────────────────────┼───────────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI (via AgentOS)                        │
│  • Chat endpoints                                               │
│  • Admin API endpoints                                          │
│  • Business configuration API                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Agno SDK Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Agent     │  │   Tools     │  │   Memory (SqliteDb)     │ │
│  │  (GPT-4o)   │  │  Functions  │  │   Conversation History  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐ │
│  │         SQLite DB           │  │    YAML Templates        │ │
│  │  • businesses               │  │  • beauty_services.yaml  │ │
│  │  • users                    │  │  • medspa_services.yaml  │ │
│  │  • services                 │  │  • fitness_services.yaml │ │
│  │  • appointments             │  │  • medical_services.yaml │ │
│  │  • leads                    │  │                          │ │
│  │  • conversations            │  │                          │ │
│  └─────────────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```
