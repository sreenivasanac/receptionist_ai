# AI Receptionist - Product Requirements Document (PRD)

## Overview

AI Receptionist chatbot for self-care businesses (salons, medspas, fitness studios, clinics). Embeddable chat widget that handles customer queries, booking, and lead capture.

**Target Industries:**
- Beauty (hair salons, barber shops, nail salons, makeup artists, brow & lash)
- Health & Wellness (medspas, wellness centers, chiropractic, massage, acupuncture)
- Medical & Specialty (plastic surgery, dermatology, dental, IV therapy, weight loss)
- Fitness (boutique gyms, pilates, yoga, personal trainers, recovery studios)

---

## V1 - Core MVP

### Admin Panel Features

1. **Signup & Authentication**
   - **Signup:** username/email + role selection
   - Role: Choose ONE of `admin` OR `business_owner` (not both)
   - No password for MVP
   - Session-based authentication
   - **Login:** username/email + role

2. **Business Setup (During Signup/First Login)**
   - Business name
   - Contact info (phone, email)
   - Address
   - Industry vertical selection (salon, medspa, fitness, medical, wellness)
   - Pre-loaded service templates based on selected vertical

3. **Business Information Management**
   - **Prompt-based input** for: services, hours, pricing, policies, FAQs
   - User enters information as free-form text/prompt
   - System parses and stores config as YAML text in database (`config_yaml` column)
   - **Storage:** YAML content stored as TEXT in database, not as separate file
   - **Runtime:** When chat session starts, YAML is fetched from DB, parsed, and held in memory for agent tools

4. **Website Import**
   - Input website URLs (multiple, with + button)
   - "Fetch Info" button to scrape content
   - Auto-parse into structured config (hours, services, pricing)
   - Store raw scraped content as fallback reference

5. **Feature Toggles**
   - Enable/disable chatbot capabilities per business

6. **Embed Code & Demo**
   - **Embed Script Tag:** Display `<script>` tag with business ID parameter
     ```html
     <script src="https://widget.keystone.ai/chat.js" data-business-id="YOUR_BUSINESS_ID"></script>
     ```
   - **Chatbot Demo Page:** Business owner can test the chatbot as a customer would see it
   - Preview widget with live business configuration

7. **Staff Management**
   - Add/edit/remove staff members
   - Fields: name
   - Staff will be used for appointment scheduling

### Chat Widget Features

1. **Embeddable widget**
   - Vanilla JS implementation
   - Single `<script>` tag embed with `data-business-id` parameter
   - Copy-paste ready from admin panel

2. **Business info queries**
   - Hours, pricing, services, location, policies
   - FAQs

3. **Greeting & general conversation**
   - Welcome message
   - Handle unclear queries gracefully

4. **Conversation context retention**
   - Within session memory

5. **Customer Information Collection**
   - Collect customer details when needed (e.g., for booking, lead capture)
   - Fields: first name, last name, email, phone number
   - Progressive collection (ask only what's needed for the action)

### Backend (V1)

1. FastAPI + Agno AgentOS setup
2. SQLite schema: businesses, users, services, conversations
3. `get_business_info` tool implementation
4. **Business Config Loading:**
   - On chat session init: fetch `config_yaml` from `businesses` table by `business_id`
   - Parse YAML text into Python dict/object
   - Hold parsed config in session memory for agent tool access
   - Agent tools query this in-memory config (no repeated DB calls)

### V1 Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_business_info` | `query_type: str` (hours/services/pricing/location/policies/faqs), `specific_item: str?` | Business data dict |
| `collect_customer_info` | `fields_needed: list[str]` (first_name/last_name/email/phone), `reason: str` | `{collected_fields: {...}, missing_fields: [...]}` |

---

## V2 - Booking & Lead Capture

### Admin Panel (V2 Additions)

1. **Leads Dashboard**
   - View captured leads
   - Fields: name, contact info, interest, date captured
   - Mark as contacted/converted

2. **Appointments List**
   - View all bookings
   - Filter by date, service, status
   - Mark as completed/no-show

3. **Waitlist Management**
   - View waitlist entries
   - Contact customers when slots open

4. **FAQ Management**
   - Add/edit custom Q&A pairs
   - Override default FAQs

5. **Customer List Management**
   - **Upload Customer List:** CSV file upload with format: `first_name, last_name, email, mobile_number`
   - View/search customer list
   - Edit individual customer records
   - Delete customers

6. **SMS Marketing (Mock)**
   - Compose SMS message
   - Select recipients (all customers, filtered by criteria)
   - Send marketing SMS (fake/mock - no actual SMS integration)
   - View sent campaigns history
   - Track delivery status (mock data)

### Chat Widget (V2 Additions)

1. **Calendar UI Component**
   - Interactive date/time picker rendered in chat
   - Visual slot selection instead of text-only
   - Shows available times highlighted

2. **Appointment scheduling flow**
   - Check availability → select slot via calendar → collect customer info → confirm booking

3. **Lead capture flow**
   - Triggered by consultation requests, corporate inquiries, etc.
   - Collect: name, email, phone, interest, notes

4. **Waitlist signup**
   - When preferred slots unavailable
   - Notify when slots open

5. **Cancel appointment**
   - Confirm cancellation

6. **Reschedule appointment**
   - Find existing booking
   - Select new slot
   - Confirm change

7. **Multi-turn conversation**
   - Slot filling across turns
   - Context retention for partial bookings

8. **Returning Customer Recognition**
   - Identify returning customers by phone/email
   - Personalized greetings: "Welcome back, Sarah!"
   - Show visit history summary: "Your last visit was a Deep Tissue Massage on Nov 15th"
   - Rebooking prompts: "It's been 6 weeks since your last facial. Ready to schedule your next one?"
   - Quick rebook: Offer to book same service with same staff

### Backend (V2 Additions)

1. Conversation memory (SQLite-backed via Agno)
2. Mock calendar system for availability
3. Appointments table
4. Leads table
5. Waitlist table

### V2 Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `check_availability` | `service_id: str`, `date_range: str`, `time_preference: str?`, `staff_id: str?` | `{slots: [...], calendar_ui_data: {...}}` |
| `book_appointment` | `service_id: str`, `slot_id: str`, `customer_name: str`, `customer_phone: str`, `customer_email: str?` | `{confirmation_id, details}` |
| `capture_lead` | `name: str`, `email: str?`, `phone: str?`, `interest: str`, `notes: str?`, `company: str?` | `{lead_id}` |
| `add_to_waitlist` | `service_id: str`, `preferred_dates: list`, `preferred_times: list`, `contact_method: str` | `{waitlist_position}` |
| `cancel_appointment` | `appointment_id: str?`, `customer_phone: str` | `{cancelled: bool, message}` |
| `reschedule_appointment` | `appointment_id: str`, `new_slot_id: str` | `{new_confirmation}` |
| `identify_customer` | `phone: str?`, `email: str?` | `{customer_id, name, is_returning, visit_count, last_visit}` |
| `get_customer_history` | `customer_id: str` | `{visits: [{date, service, staff}], total_visits, favorite_service}` |

---

## V3 - Intelligence & Polish

### Admin Panel (V3 Additions)

1. **Conversation History**
   - View full chat transcripts per session
   - Search conversations
   - Export capability

2. **Analytics Dashboard**
   - Leads count (daily/weekly/monthly)
   - Appointments booked
   - Conversation metrics (volume, avg length)
   - Conversion rates

3. **Custom Prompt/Tone**
   - Configure AI personality
   - Add special instructions
   - Set business-specific phrases

4. **Policies Editor**
   - Cancellation policy
   - Deposit requirements
   - Walk-in policy
   - Custom policies

### Chat Widget (V3 Additions)

1. **Service recommendations**
   - AI suggests services based on customer goals/concerns
   - Explains why each service fits
   - Offers to book recommended services

2. **Proactive follow-ups**
   - "Would you like to book?" after answering questions
   - Suggest related services
   - Prompt for feedback

3. **Custom Workflow Builder**
   - Visual/template-based workflow builder in Admin Panel
   - **Trigger types:**
     - Keyword match (e.g., customer mentions "wedding", "corporate")
     - Customer segment (new vs returning, visit count)
     - Time-based (first message, after X minutes idle)
   - **Actions:**
     - Apply discount automatically
     - Capture as lead with specific interest
     - Route to human/escalate
     - Send custom message
     - Offer specific service
   - **Pre-built workflow templates:**
     - Birthday discount workflow
     - New customer welcome offer
     - Bridal/event inquiry capture
     - Membership inquiry routing
     - Promo code redemption
     - Loyalty rewards check

4. **Improved NLU**
   - Better handling of edge cases
   - Typo tolerance
   - Multi-part question handling

### Backend (V3 Additions)

1. `recommend_service` tool with matching logic
2. Analytics aggregation queries
3. Webhook placeholders for future integrations

### V3 Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `recommend_service` | `goals: str`, `concerns: str?`, `preferences: str?`, `budget: str?` | `{recommendations: [{service, reason, price}]}` |
| `execute_workflow` | `workflow_id: str`, `context: dict` | `{actions_taken: [...], result: str}` |

---

## V4 - Business Intelligence & Insights

### Admin Panel (V4 Additions)

1. **Actionable Insights Dashboard**
   - **Demand Signals:** "Customers asked about 'microblading' 12 times this month - you don't currently offer this service"
   - **Scheduling Optimization:** "Tuesday 2-4 PM has 40% fewer bookings than other slots - consider running a promotion"
   - **Conversion Insights:** "23 customers asked about pricing but didn't book - consider adding a first-visit discount"
   - **Staff Performance:** "Sarah has 95% rebooking rate vs team average of 72%"

2. **Unanswered Questions Report**
   - Log questions the AI couldn't answer confidently
   - Categorize by topic (pricing, services, policies, etc.)
   - Suggest FAQ additions based on frequency

3. **Customer Behavior Analytics**
   - Peak inquiry times
   - Most requested services
   - Common customer journeys (inquiry → booking patterns)
   - Drop-off points in conversation

4. **Revenue Insights**
   - Booking value trends
   - Service popularity ranking
   - Customer lifetime value estimates
   - Lead-to-customer conversion timeline

### Backend (V4 Additions)

1. Analytics aggregation jobs (daily/weekly)
2. Insight generation algorithms
3. Unanswered questions logging and categorization
4. Trend detection queries

### V4 Tools

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_business_insights` | `insight_type: str`, `date_range: str?` | `{insights: [{type, message, data, recommendation}]}` |
| `get_unanswered_questions` | `limit: int?`, `category: str?` | `{questions: [{text, count, suggested_answer}]}` |

---

## Tool Schema Reference (All Versions)

### get_business_info (V1)

```python
def get_business_info(query_type: str, specific_item: str = None) -> dict:
    """
    Retrieve business information.
    
    Args:
        query_type: One of "hours", "services", "pricing", "location", "policies", "faqs"
        specific_item: Optional - specific service name, day, or FAQ topic
    
    Returns:
        Relevant business information as structured data
    """
```

### collect_customer_info (V1)

```python
def collect_customer_info(
    fields_needed: list[str],
    reason: str
) -> dict:
    """
    Collect customer information when needed for booking, leads, etc.
    
    Args:
        fields_needed: List of fields to collect - "first_name", "last_name", "email", "phone"
        reason: Why we need this info (e.g., "to complete your booking", "to send confirmation")
    
    Returns:
        {
            "collected_fields": {"first_name": "...", "email": "..."},
            "missing_fields": ["phone"]  # Fields still needed
        }
    """
```

### check_availability (V2)

```python
def check_availability(
    service_id: str,
    date_range: str,
    time_preference: str = None,
    staff_id: str = None
) -> dict:
    """
    Check available appointment slots.
    
    Args:
        service_id: ID of the service to book
        date_range: e.g., "this week", "tomorrow", "Dec 15-20"
        time_preference: e.g., "morning", "after 5pm", "afternoon"
        staff_id: Optional specific staff member
    
    Returns:
        {
            "slots": [{"id", "date", "time", "staff_name", "duration"}],
            "calendar_ui_data": {...}  # For rendering interactive calendar in chat
        }
    """
```

### book_appointment (V2)

```python
def book_appointment(
    service_id: str,
    slot_id: str,
    customer_name: str,
    customer_phone: str,
    customer_email: str = None
) -> dict:
    """
    Book a confirmed appointment.
    
    Returns:
        {"confirmation_id", "service", "date", "time", "staff", "message"}
    """
```

### capture_lead (V2)

```python
def capture_lead(
    name: str,
    interest: str,
    email: str = None,
    phone: str = None,
    notes: str = None,
    company: str = None
) -> dict:
    """
    Capture lead for sales follow-up.
    
    Returns:
        {"lead_id", "message"}
    """
```

### add_to_waitlist (V2)

```python
def add_to_waitlist(
    service_id: str,
    preferred_dates: list[str],
    preferred_times: list[str],
    contact_method: str
) -> dict:
    """
    Add customer to waitlist.
    
    Returns:
        {"waitlist_position", "message"}
    """
```

### cancel_appointment (V2)

```python
def cancel_appointment(
    customer_phone: str,
    appointment_id: str = None
) -> dict:
    """
    Cancel an existing appointment.
    
    Returns:
        {"cancelled": bool, "message"}
    """
```

### reschedule_appointment (V2)

```python
def reschedule_appointment(
    appointment_id: str,
    new_slot_id: str
) -> dict:
    """
    Reschedule to a new time slot.
    
    Returns:
        {"new_confirmation_id", "new_date", "new_time", "message"}
    """
```

### identify_customer (V2)

```python
def identify_customer(
    phone: str = None,
    email: str = None
) -> dict:
    """
    Identify if a customer is new or returning.
    
    Args:
        phone: Customer phone number
        email: Customer email address
    
    Returns:
        {
            "customer_id": "...",
            "name": "Sarah Johnson",
            "is_returning": true,
            "visit_count": 5,
            "last_visit": {"date": "2024-11-15", "service": "Deep Tissue Massage"}
        }
    """
```

### get_customer_history (V2)

```python
def get_customer_history(
    customer_id: str
) -> dict:
    """
    Get visit history for a returning customer.
    
    Returns:
        {
            "visits": [{"date", "service", "staff", "notes"}],
            "total_visits": 5,
            "favorite_service": "Deep Tissue Massage",
            "average_visit_frequency_days": 42
        }
    """
```

### recommend_service (V3)

```python
def recommend_service(
    goals: str,
    concerns: str = None,
    preferences: str = None,
    budget: str = None
) -> dict:
    """
    Recommend services based on customer needs.
    
    Returns:
        {
            "recommendations": [
                {"service_id", "name", "price", "reason"}
            ]
        }
    """
```

### execute_workflow (V3)

```python
def execute_workflow(
    workflow_id: str,
    context: dict
) -> dict:
    """
    Execute a custom workflow based on triggers.
    
    Args:
        workflow_id: ID of the workflow to execute
        context: Current conversation context and customer data
    
    Returns:
        {
            "actions_taken": ["applied_discount", "sent_message"],
            "result": "Applied 20% birthday discount"
        }
    """
```

### get_business_insights (V4)

```python
def get_business_insights(
    insight_type: str,
    date_range: str = None
) -> dict:
    """
    Get actionable business insights.
    
    Args:
        insight_type: One of "demand", "scheduling", "conversion", "performance"
        date_range: e.g., "last_week", "last_month", "last_quarter"
    
    Returns:
        {
            "insights": [
                {
                    "type": "demand_signal",
                    "message": "Customers asked about 'microblading' 12 times",
                    "data": {"keyword": "microblading", "count": 12},
                    "recommendation": "Consider adding this service"
                }
            ]
        }
    """
```

---

## Industry Verticals (Pre-loaded Templates)

### 1. Beauty
- Hair salons, barber shops, nail salons, makeup artists, brow & lash studios
- **Default services:** Haircut, Color, Highlights, Manicure, Pedicure, Waxing, etc.
- **Common FAQs:** Walk-ins, payment methods, parking
- **Lead triggers:** Bridal packages, events

### 2. Health & Wellness
- Medspas, wellness centers, chiropractic, massage, acupuncture
- **Default services:** Massage (various types), Facials, Botox, Fillers, Acupuncture
- **Common FAQs:** First visit preparation, insurance, consultations
- **Lead triggers:** Membership inquiries, corporate wellness

### 3. Medical & Specialty
- Plastic surgery, dermatology, dental, IV therapy, weight loss clinics
- **Default services:** Consultations, Procedures (varies by type)
- **Common FAQs:** Financing, recovery time, credentials
- **Lead triggers:** All services (require consultation)

### 4. Fitness
- Boutique gyms, pilates, yoga, personal trainers, recovery studios
- **Default services:** Classes, Personal Training, Memberships, Recovery sessions
- **Common FAQs:** Class schedule, membership options, trial classes
- **Lead triggers:** Membership inquiries, corporate packages

Each vertical comes with:
- Default service list with typical pricing
- Common FAQs
- Relevant lead capture triggers
- Appropriate tone/prompt defaults

---

## Database Schema (High-Level)

### businesses
- id, name, type (vertical), address, phone, email, website
- config_yaml (TEXT) -- full business config stored as YAML string (hours, services, pricing, policies, FAQs, etc.)
- created_at, updated_at

### users
- id, username, email, role (ONE of: admin | business_owner), business_id
- created_at, last_login

### services
- id, business_id, name, description, duration_minutes, price
- requires_consultation, is_active
- created_at, updated_at

### staff (V1)
- id, business_id, name, role_title
- services_offered (JSON - list of service_ids)
- is_active
- created_at, updated_at

### appointments (V2)
- id, business_id, service_id, customer_name, customer_phone, customer_email
- date, time, duration, staff_name, status
- created_at, updated_at

### leads (V2)
- id, business_id, name, email, phone, interest, notes, company
- status (new/contacted/converted)
- created_at, updated_at

### waitlist (V2)
- id, business_id, service_id, customer_name, customer_contact
- preferred_dates, preferred_times, status
- created_at

### conversations
- id, business_id, session_id, messages (JSON)
- created_at, updated_at

### customers
- id, business_id, first_name, last_name, email, phone
- visit_count, last_visit_date, favorite_service_id
- created_at, updated_at

### sms_campaigns (V2)
- id, business_id, message, recipient_filter (JSON)
- status (draft/sent), sent_at, recipient_count
- created_at

### workflows (V3)
- id, business_id, name, description
- trigger_type (keyword/segment/time), trigger_config (JSON)
- actions (JSON - list of action configs)
- is_active
- created_at, updated_at

### unanswered_questions (V4)
- id, business_id, question_text, category
- occurrence_count, last_asked_at
- suggested_answer, is_resolved
- created_at

### scraped_content
- id, business_id, url, raw_content, parsed_data (JSON)
- scraped_at
