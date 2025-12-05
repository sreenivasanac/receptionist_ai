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

## Project Folder Structure

```
receptionist_ai/
│
├── backend/                          # Python backend (FastAPI + Agno)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry, AgentOS setup
│   │   ├── config.py                 # Settings, environment config
│   │   │
│   │   ├── api/                      # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── chat.py               # POST /chat - widget chat endpoint
│   │   │   ├── admin.py              # Admin panel CRUD endpoints
│   │   │   ├── business.py           # Business config API
│   │   │   └── auth.py               # Login/signup endpoints
│   │   │
│   │   ├── agent/                    # Agno agent configuration
│   │   │   ├── __init__.py
│   │   │   ├── receptionist.py       # Main Agent definition
│   │   │   └── prompts.py            # System prompts per vertical
│   │   │
│   │   ├── tools/                    # Agent tools (by version)
│   │   │   ├── __init__.py
│   │   │   ├── business_info.py      # V1: get_business_info
│   │   │   ├── customer_info.py      # V1: collect_customer_info
│   │   │   ├── booking.py            # V2: check_availability, book_appointment
│   │   │   ├── leads.py              # V2: capture_lead, add_to_waitlist
│   │   │   ├── customers.py          # V2: identify_customer, get_customer_history
│   │   │   ├── recommendations.py    # V3: recommend_service
│   │   │   ├── workflows.py          # V3: execute_workflow
│   │   │   └── insights.py           # V4: get_business_insights
│   │   │
│   │   ├── models/                   # Pydantic models & DB schemas
│   │   │   ├── __init__.py
│   │   │   ├── business.py           # Business, scraped_content
│   │   │   ├── user.py               # User (admin/business_owner)
│   │   │   ├── service.py            # Service definitions
│   │   │   ├── staff.py              # Staff members
│   │   │   ├── appointment.py        # V2: Appointments
│   │   │   ├── lead.py               # V2: Leads, waitlist
│   │   │   ├── customer.py           # Customers
│   │   │   ├── conversation.py       # Chat sessions
│   │   │   ├── campaign.py           # V2: SMS campaigns
│   │   │   └── workflow.py           # V3: Workflows
│   │   │
│   │   ├── services/                 # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── scraper.py            # Website scraping (httpx + BS4)
│   │   │   ├── config_parser.py      # YAML parsing & validation
│   │   │   ├── calendar.py           # V2: Mock calendar/availability
│   │   │   ├── sms.py                # V2: Mock SMS service
│   │   │   └── analytics.py          # V3/V4: Analytics aggregation
│   │   │
│   │   └── db/                       # Database layer
│   │       ├── __init__.py
│   │       ├── database.py           # SQLite connection setup
│   │       └── init_db.py            # Schema initialization
│   │
│   ├── data/
│   │   ├── templates/                # Industry vertical templates
│   │   │   ├── beauty.yaml           # Hair salons, barbers, nail salons
│   │   │   ├── wellness.yaml         # Medspas, massage, chiro
│   │   │   ├── medical.yaml          # Plastic surgery, dental, derm
│   │   │   └── fitness.yaml          # Gyms, yoga, pilates
│   │   │
│   │   └── receptionist.db           # SQLite database file
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_api/
│   │   ├── test_tools/
│   │   └── test_services/
│   │
│   ├── pyproject.toml                # Python deps (uv)
│   ├── .env.example                  # Environment template
│   └── .python-version               # Python version for uv
│
├── frontend/
│   ├── widget/                       # Embeddable chat widget
│   │   ├── src/
│   │   │   ├── chat.js               # Main widget logic
│   │   │   ├── styles.css            # Widget styles
│   │   │   ├── api.js                # Backend API client
│   │   │   └── components/           # V2: Calendar picker, etc.
│   │   │
│   │   ├── dist/                     # Built output
│   │   │   └── chat.js               # Single embeddable bundle
│   │   │
│   │   ├── index.html                # Local dev/test page
│   │   └── build.js                  # Build script (esbuild)
│   │
│   └── admin/                        # Admin panel (React)
│       ├── src/
│       │   ├── App.tsx
│       │   ├── main.tsx
│       │   │
│       │   ├── components/
│       │   │   ├── layout/           # Sidebar, header, etc.
│       │   │   ├── business/         # Business setup, config editor
│       │   │   ├── staff/            # Staff management
│       │   │   ├── leads/            # V2: Leads dashboard
│       │   │   ├── appointments/     # V2: Appointments list
│       │   │   ├── customers/        # V2: Customer list, SMS
│       │   │   ├── conversations/    # V3: Chat history viewer
│       │   │   ├── analytics/        # V3/V4: Dashboards
│       │   │   └── workflows/        # V3: Workflow builder
│       │   │
│       │   ├── pages/                # Route pages
│       │   │   ├── Dashboard.tsx
│       │   │   ├── BusinessSetup.tsx
│       │   │   ├── Leads.tsx
│       │   │   ├── Appointments.tsx
│       │   │   ├── Customers.tsx
│       │   │   ├── Analytics.tsx
│       │   │   └── Settings.tsx
│       │   │
│       │   ├── hooks/                # Custom React hooks
│       │   ├── services/             # API client (fetch/axios)
│       │   ├── types/                # TypeScript types
│       │   └── utils/                # Helpers
│       │
│       ├── public/
│       ├── package.json
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       └── vite.config.ts
│
├── agentic_development_docs/         # Project documentation
│   ├── business_plan/
│   │   ├── 0_keystone_business_idea.md
│   │   └── 1_target_businesses_keystone.md
│   │
│   └── project_design_plan/
│       ├── 0_ideation.md
│       ├── 2_initial_plan.md         # PRD
│       └── 3_tech_stack.md           # This file
│
├── README.md
├── .gitignore
└── docker-compose.yml                # Optional: local dev setup
```

### Folder Structure Notes

| Folder | Purpose |
|--------|---------|
| `backend/app/api/` | FastAPI route handlers, thin layer calling services/tools |
| `backend/app/agent/` | Agno Agent definition, system prompts |
| `backend/app/tools/` | Agent tool implementations (one file per tool group) |
| `backend/app/models/` | Pydantic models for API + DB schemas |
| `backend/app/services/` | Business logic (scraping, analytics, etc.) |
| `backend/data/templates/` | YAML templates for industry verticals |
| `frontend/widget/` | Standalone embeddable chat widget |
| `frontend/admin/` | React admin panel for business owners |

---
