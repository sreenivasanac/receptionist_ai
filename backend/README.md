# AI Receptionist Backend

Keystone AI Receptionist - Backend API for self-care business chatbot.

## Setup

```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run the server
uv run python -m app.main
```

Server runs at http://localhost:8001

## Architecture

```
app/
├── api/                  # FastAPI route handlers
│   ├── auth.py          # Authentication (signup, login)
│   ├── business.py      # Business config management
│   ├── chat.py          # Chat message handling
│   ├── admin.py         # Staff management
│   ├── appointments.py  # V2: Appointment CRUD
│   ├── customers.py     # V2: Customer CRUD + CSV import
│   ├── leads.py         # V2: Lead & waitlist management
│   ├── campaigns.py     # V2: SMS campaign management (mock)
│   ├── faqs.py          # V2: FAQ management
│   ├── analytics.py     # V3: Dashboard metrics & stats
│   ├── workflows.py     # V3: Custom workflow management
│   └── conversations.py # V3: Conversation history & export
├── agent/
│   ├── receptionist.py  # Agno agent with V1-V3 tools
│   └── prompts.py       # System prompts
├── tools/
│   ├── booking.py       # V2: Availability, booking tools
│   ├── customers.py     # V2: Customer identification tools
│   ├── leads.py         # V2: Lead capture, waitlist tools
│   ├── recommendations.py # V3: Service recommendation engine
│   └── workflows.py     # V3: Workflow trigger & execution
├── repositories/        # Data access layer
│   ├── base.py          # Base repository with CRUD operations
│   ├── analytics.py     # V3: Analytics queries
│   ├── workflows.py     # V3: Workflow CRUD & templates
│   └── ...              # Other entity repositories
├── services/
│   └── calendar.py      # Calendar service with cancellation recovery
├── models/              # Pydantic models
└── db/
    └── database.py      # SQLite database with V1-V3 tables
```

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user & business
- `POST /auth/login` - Login

### Business
- `GET /business/{id}` - Get business details
- `PUT /business/{id}/config` - Update business config (YAML)

### Chat
- `POST /chat/message` - Send chat message
- `GET /chat/greeting/{business_id}` - Get greeting message
- `GET /chat/history/{business_id}/{session_id}` - Get conversation history

### Admin - Staff
- `GET /admin/{business_id}/staff` - List staff
- `POST /admin/{business_id}/staff` - Add staff member

### V2 - Appointments
- `GET /admin/{business_id}/appointments` - List appointments (with filters)
- `POST /admin/{business_id}/appointments` - Create appointment
- `GET /admin/{business_id}/appointments/{id}` - Get appointment
- `PUT /admin/{business_id}/appointments/{id}` - Update appointment
- `DELETE /admin/{business_id}/appointments/{id}` - Delete appointment

### V2 - Customers
- `GET /admin/{business_id}/customers` - List customers (with search)
- `POST /admin/{business_id}/customers` - Create customer
- `POST /admin/{business_id}/customers/import` - Import from CSV
- `GET /admin/{business_id}/customers/{id}` - Get customer
- `PUT /admin/{business_id}/customers/{id}` - Update customer

### V2 - Leads
- `GET /admin/{business_id}/leads` - List leads (with status filter)
- `POST /admin/{business_id}/leads` - Create lead
- `PUT /admin/{business_id}/leads/{id}` - Update lead

### V2 - Waitlist
- `GET /admin/{business_id}/waitlist` - List waitlist entries
- `POST /admin/{business_id}/waitlist` - Add to waitlist
- `PUT /admin/{business_id}/waitlist/{id}` - Update entry

### V2 - SMS Campaigns (Mock)
- `GET /admin/{business_id}/campaigns` - List campaigns
- `POST /admin/{business_id}/campaigns` - Create campaign
- `POST /admin/{business_id}/campaigns/{id}/send` - Send campaign

### V2 - FAQs
- `GET /admin/{business_id}/faqs` - List FAQs
- `POST /admin/{business_id}/faqs` - Create FAQ
- `PUT /admin/{business_id}/faqs/{id}` - Update FAQ
- `DELETE /admin/{business_id}/faqs/{id}` - Delete FAQ

### V3 - Analytics
- `GET /analytics/overview/{business_id}` - Complete dashboard metrics
- `GET /analytics/summary/{business_id}` - Summary statistics
- `GET /analytics/leads/{business_id}` - Lead stats by status, source, day
- `GET /analytics/appointments/{business_id}` - Appointment stats by status, service
- `GET /analytics/conversations/{business_id}` - Conversation metrics, peak hours

### V3 - Conversations
- `GET /conversations/{business_id}` - List/search conversations
- `GET /conversations/{business_id}/{session_id}` - Get full conversation
- `GET /conversations/{business_id}/{session_id}/export` - Export transcript (JSON/CSV)
- `GET /conversations/{business_id}/export/all` - Export all conversations

### V3 - Workflows
- `GET /workflows/{business_id}` - List all workflows
- `POST /workflows/{business_id}` - Create custom workflow
- `GET /workflows/{business_id}/templates` - Get pre-built workflow templates
- `POST /workflows/{business_id}/from-template` - Create from template
- `POST /workflows/{business_id}/{id}/toggle` - Enable/disable workflow
- `PUT /workflows/{business_id}/{id}` - Update workflow
- `DELETE /workflows/{business_id}/{id}` - Delete workflow

## Agent Tools (V2)

The AI agent has access to these tools for handling conversations:

**Booking Tools:**
- `check_availability` - Check available time slots for services
- `book_appointment` - Book an appointment
- `cancel_appointment` - Cancel existing appointment
- `reschedule_appointment` - Reschedule appointment

**Customer Tools:**
- `identify_customer` - Recognize returning customers
- `get_customer_history` - Get visit history
- `suggest_rebooking` - Suggest rebooking for returning customers

**Lead Tools:**
- `capture_lead` - Capture sales inquiry
- `add_to_waitlist` - Add customer to waitlist

## Agent Tools (V3)

**Recommendation Tools:**
- `recommend_service` - Suggest services based on customer goals/concerns

**Workflow Tools:**
- `check_for_special_offers` - Trigger workflows based on keywords (birthday, wedding, corporate)

## Database Tables

- `users` - Admin users
- `businesses` - Business profiles and config
- `staff` - Staff members
- `conversations` - Chat session storage
- `customers` - V2: Customer records
- `appointments` - V2: Appointment bookings
- `leads` - V2: Sales leads
- `waitlist` - V2: Waitlist entries
- `sms_campaigns` - V2: Marketing campaigns
- `workflows` - V3: Custom workflow definitions
- `waitlist_notifications` - V3: Cancellation recovery tracking
- `unanswered_questions` - V3: Questions AI couldn't answer (for V4 insights)
