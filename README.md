# AI Receptionist - Keystone

AI-powered receptionist chatbot for self-care businesses (salons, medspas, fitness studios, clinics).

## Features (V1 - Implemented)

- **Business Information Queries** - Hours, pricing, services, location, policies, FAQs
- **Embeddable Chat Widget** - Single script tag to add to any website
- **Admin Panel** - Configure business info, manage staff, preview chatbot
- **Industry Templates** - Pre-loaded configs for beauty, wellness, medical, fitness
- **Conversation Context** - Session-based memory for natural conversations

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, Agno SDK, SQLite
- **Frontend**: React + Tailwind (Admin), Vanilla JS (Widget)
- **AI**: OpenAI GPT-4o-mini

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run server
uv run python -m app.main
```

The API will be available at http://localhost:8000

### 2. Admin Panel Setup

```bash
cd frontend/admin

# Install dependencies
pnpm install

# Run dev server
pnpm dev
```

Admin panel at http://localhost:3000

### 3. Test the Widget

1. Sign up via the admin panel (creates a business)
2. Go to Settings to get your embed code
3. Open `frontend/widget/index.html` in a browser
4. Or add the embed code to any HTML page

## Project Structure

```
receptionist_ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── agent/        # Agno agent & prompts
│   │   ├── tools/        # Agent tools
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic
│   │   └── db/           # Database
│   └── data/
│       └── templates/    # Industry YAML templates
├── frontend/
│   ├── widget/           # Embeddable chat widget
│   └── admin/            # React admin panel
└── agentic_development_docs/
```

## API Endpoints

- `POST /auth/signup` - Register user & business
- `POST /auth/login` - Login
- `GET /business/{id}` - Get business details
- `PUT /business/{id}/config` - Update config (YAML)
- `POST /chat/message` - Send chat message
- `GET /chat/greeting/{id}` - Get greeting
- `GET /admin/{id}/staff` - List staff
- `POST /admin/{id}/staff` - Add staff

## Documentation

- [PRD & Technical Spec](agentic_development_docs/project_design_plan/2_initial_plan.md)
- [Business Idea](agentic_development_docs/business_plan/0_keystone_business_idea.md)
- [Target Businesses](agentic_development_docs/business_plan/1_target_businesses_keystone.md)