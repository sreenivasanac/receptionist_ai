# AI Receptionist - Keystone

AI-powered receptionist chatbot for self-care businesses (salons, medspas, fitness studios, clinics).

## Features

### V1 - Core Features
- **Business Information Queries** - Hours, pricing, services, location, policies, FAQs
- **Embeddable Chat Widget** - Single script tag to add to any website
- **Admin Panel** - Configure business info, manage staff, preview chatbot
- **Industry Templates** - Pre-loaded configs for beauty, wellness, medical, fitness
- **Conversation Context** - Session-based memory for natural conversations

### V2 - Booking & CRM (Current)
- **Appointment Booking** - Check availability, book, cancel, reschedule appointments
- **Customer Recognition** - Identify returning customers, show visit history
- **Lead Capture** - Capture sales inquiries with contact information
- **Waitlist Management** - Add customers to waitlist when no slots available
- **SMS Marketing** - Create and send SMS campaigns (mock implementation)
- **FAQ Management** - CRUD operations for business FAQs
- **Structured Chat Inputs** - Service selector, date/time picker, contact forms in widget

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
│   │   ├── api/          # FastAPI routes (auth, chat, business, appointments, leads, customers, campaigns, faqs)
│   │   ├── agent/        # Agno agent & prompts
│   │   ├── tools/        # Agent tools (booking, leads, customers)
│   │   ├── models/       # Pydantic models (appointment, lead, customer, campaign)
│   │   ├── services/     # Business logic (calendar service)
│   │   └── db/           # Database (SQLite)
│   └── data/
│       └── templates/    # Industry YAML templates
├── frontend/
│   ├── widget/           # Embeddable chat widget with structured inputs
│   └── admin/            # React admin panel (dashboard, appointments, customers, leads, waitlist, marketing)
└── agentic_development_docs/
```

## API Endpoints

### Authentication & Business
- `POST /auth/signup` - Register user & business
- `POST /auth/login` - Login
- `GET /business/{id}` - Get business details
- `PUT /business/{id}/config` - Update config (YAML)

### Chat
- `POST /chat/message` - Send chat message
- `GET /chat/greeting/{id}` - Get greeting
- `GET /chat/history/{business_id}/{session_id}` - Get chat history

### Admin - Staff & Settings
- `GET /admin/{id}/staff` - List staff
- `POST /admin/{id}/staff` - Add staff

### V2 - Appointments
- `GET /admin/{id}/appointments` - List appointments
- `POST /admin/{id}/appointments` - Create appointment
- `PUT /admin/{id}/appointments/{appt_id}` - Update appointment
- `DELETE /admin/{id}/appointments/{appt_id}` - Delete appointment

### V2 - Customers
- `GET /admin/{id}/customers` - List customers
- `POST /admin/{id}/customers` - Create customer
- `POST /admin/{id}/customers/import` - Import customers from CSV

### V2 - Leads & Waitlist
- `GET /admin/{id}/leads` - List leads
- `POST /admin/{id}/leads` - Create lead
- `GET /admin/{id}/waitlist` - List waitlist entries
- `POST /admin/{id}/waitlist` - Add to waitlist

### V2 - Campaigns & FAQs
- `GET /admin/{id}/campaigns` - List SMS campaigns
- `POST /admin/{id}/campaigns` - Create campaign
- `POST /admin/{id}/campaigns/{campaign_id}/send` - Send campaign (mock)
- `GET /admin/{id}/faqs` - List FAQs
- `POST /admin/{id}/faqs` - Create FAQ

## Documentation

- [PRD & Technical Spec](agentic_development_docs/project_design_plan/2_initial_plan.md)
- [Business Idea](agentic_development_docs/business_plan/0_keystone_business_idea.md)
- [Target Businesses](agentic_development_docs/business_plan/1_target_businesses_keystone.md)