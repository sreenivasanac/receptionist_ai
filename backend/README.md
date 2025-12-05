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
│   └── faqs.py          # V2: FAQ management
├── agent/
│   ├── receptionist.py  # Agno agent with tools
│   └── prompts.py       # System prompts
├── tools/
│   ├── booking.py       # V2: Availability, booking tools
│   ├── customers.py     # V2: Customer identification tools
│   └── leads.py         # V2: Lead capture, waitlist tools
├── services/
│   └── calendar.py      # V2: Mock calendar service
├── models/              # Pydantic models
│   ├── appointment.py   # Appointment, TimeSlot, BookingConfirmation
│   ├── customer.py      # Customer, CustomerHistory
│   ├── lead.py          # Lead, WaitlistEntry
│   └── campaign.py      # Campaign, RecipientFilter
└── db/
    └── database.py      # SQLite database with V2 tables
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
