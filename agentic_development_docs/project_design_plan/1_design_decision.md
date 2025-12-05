# AI Receptionist Chatbot - High-Level Design

## Overview

The Keystone AI Receptionist is a conversational chatbot that handles customer interactions for self-care businesses (salons, medspas, fitness studios, clinics). It needs to understand what customers want, route them to the right workflow, and execute actions like answering questions, booking appointments, or capturing leads.

---

## Architecture Approaches

### Option A: LLM-First with Function Calling (Recommended for MVP)

Use a modern LLM (GPT-4, Claude) with **function/tool calling** as the primary architecture. Each business capability becomes a "tool" the AI can invoke.

```
Customer Message
       ↓
   LLM Engine (with system prompt + tools)
       ↓
   Decides: Which tool to call? What parameters?
       ↓
   Execute Tool → Return Result → Generate Response
```

**Why this approach:**
- No training data required — works out-of-the-box with good prompts
- Handles natural language variation, typos, multi-part questions
- Easy to add new capabilities (just add a new tool/function)
- Single system handles intent + slot extraction + response generation

### Option B: Traditional NLU + Dialogue Manager (Rasa-style)

Use explicit intent classifiers and slot-filling with predefined dialogue flows.

**When to consider:**
- Need strict, deterministic behavior for compliance
- Have hundreds of intents with lots of training data
- Latency/cost constraints require lightweight classifiers

**For Keystone MVP:** Option A is simpler and faster to build.

---

## How Intent Recognition Works

### LLM Function Calling as Intent Layer

Instead of classifying into "intents," we define **tools** that represent business actions. The LLM decides which tool to call based on the user message.

**Example Tools for AI Receptionist:**

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `get_business_info` | Answer questions about hours, pricing, services, location | `query_type`, `specific_question` |
| `check_availability` | Look up available appointment slots | `service_type`, `preferred_date`, `preferred_time` |
| `book_appointment` | Book an appointment for the customer | `service`, `date`, `time`, `customer_name`, `customer_phone` |
| `capture_lead` | Collect contact info for sales follow-up | `name`, `email`, `phone`, `interest`, `notes` |
| `add_to_waitlist` | Add customer to waitlist for a slot | `service`, `preferred_times`, `contact_method` |
| `recommend_service` | Suggest services based on customer needs | `customer_goals`, `concerns`, `preferences` |
| `general_response` | Handle general conversation, greetings, unclear queries | `message` |

### How the LLM Decides

1. **System Prompt** tells the AI its role and when to use each tool:
   ```
   You are a friendly receptionist for {business_name}, a {business_type}.
   
   Use get_business_info when customer asks about hours, pricing, services, parking, policies.
   Use check_availability when customer wants to know available times.
   Use book_appointment ONLY after customer confirms a specific slot.
   Use capture_lead when customer expresses interest in services requiring consultation or sales follow-up.
   ...
   ```

2. **Tool Descriptions** guide the model:
   ```
   book_appointment: "Book a confirmed appointment. Only call this after 
   the customer has selected a specific date/time and provided their name."
   ```

3. **LLM Reasoning**: Given the message "Do you have anything Saturday afternoon?", the LLM:
   - Recognizes this is asking about availability (not booking yet)
   - Calls `check_availability(preferred_date="Saturday", preferred_time="afternoon")`
   - Receives available slots from backend
   - Generates natural response listing options

---

## Workflow Decision Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Customer Message                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LLM with Tools                               │
│  • Analyzes message + conversation history                      │
│  • Considers business context (loaded from config)              │
│  • Decides: call tool OR respond directly                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
            ┌─────────────────┴─────────────────┐
            ↓                                   ↓
    [Tool Call Needed]                  [Direct Response]
            ↓                                   ↓
┌───────────────────────┐           ┌───────────────────────┐
│  Execute Tool         │           │  Generate Response    │
│  • get_business_info  │           │  (greetings, thanks,  │
│  • check_availability │           │   clarifications)     │
│  • book_appointment   │           └───────────────────────┘
│  • capture_lead       │
│  • etc.               │
└───────────────────────┘
            ↓
┌───────────────────────────────────────────────────────────────┐
│                    Tool Result                                │
│  (available slots, booking confirmation, business info, etc.) │
└───────────────────────────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────────────────────────┐
│              LLM Generates Final Response                     │
│  • Uses tool result to craft natural, helpful reply           │
│  • Maintains conversation context                             │
│  • May prompt for next step (e.g., "Would you like to book?") │
└───────────────────────────────────────────────────────────────┘
```

---

## Multi-Turn Conversation & Slot Filling

The LLM naturally handles multi-turn conversations and missing information:

**Example: Booking Flow**
```
Customer: "I want to book a haircut"
AI: [calls check_availability(service="haircut")] 
    → Missing date/time, asks: "Sure! When would you like to come in?"

Customer: "Tomorrow afternoon"
AI: [calls check_availability(service="haircut", date="tomorrow", time="afternoon")]
    → Returns slots: "I have 2 PM, 3:30 PM, and 4 PM available. Which works best?"

Customer: "3:30"
AI: [needs name/phone to book]
    → "Great! Can I get your name and phone number to confirm the booking?"

Customer: "John, 555-1234"
AI: [calls book_appointment(service="haircut", date="tomorrow", time="3:30 PM", 
                           customer_name="John", customer_phone="555-1234")]
    → "Perfect! You're booked for a haircut tomorrow at 3:30 PM. See you then, John!"
```

The LLM tracks what's been collected and what's still needed — no explicit state machine required.

---

## Business Configuration

Each business can configure:

1. **Business Profile** — Name, type, hours, location, services, pricing
2. **Enabled Features** — Which tools/capabilities are active
3. **Custom Prompts** — Tone, special instructions, FAQs
4. **Workflow Rules** — When to capture leads, confirmation requirements

**Example Config Structure:**
```yaml
business:
  name: "Glow Medspa"
  type: "medspa"
  hours:
    monday: "9 AM - 7 PM"
    saturday: "10 AM - 4 PM"
    sunday: "Closed"
  
services:
  - name: "Botox"
    duration: 30
    price: 350
    requires_consultation: true
  - name: "Facial"
    duration: 60
    price: 120

features:
  appointment_scheduling: true
  lead_capture: true
  waitlist: true
  service_recommendations: true

lead_capture_triggers:
  - "consultation"
  - "corporate"
  - "pricing for multiple"
```

---

## Technology Stack Recommendation (MVP)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **LLM** | OpenAI GPT-4 or Claude | Best function calling, natural conversation |
| **Backend** | Python (FastAPI) | Simple, async, good LLM library support |
| **LLM Framework** | LangChain or direct API | LangChain for tool orchestration, or raw API for simplicity |
| **Data Storage** | JSON/YAML files (MVP) | Business config, mock bookings, leads |
| **Frontend** | Simple chat widget | Embed on business website |

### Why NOT Rasa/Botpress for MVP:
- Requires training data and NLU pipeline setup
- More infrastructure overhead
- LLM function calling achieves same result faster for <50 intents
- Can migrate later if needed for scale/compliance

---

## Libraries to Consider

| Library | Use Case |
|---------|----------|
| **Agno**. | Model-agnostic orchestration framework|
| **LangChain** | Tool orchestration, conversation memory, prompt templates |
| **OpenAI SDK** | Direct GPT API with function calling |
| **Anthropic SDK** | Claude API with tool use |
| **Pydantic** | Structured tool parameter validation |
| **FastAPI** | REST API backend |

---

## Key Design Decisions

1. **LLM-first, not NLU-first** — Let the LLM handle intent + entities + response in one pass
2. **Tools = Capabilities** — Each feature is a callable tool with clear parameters
3. **Config-driven** — Business-specific behavior loaded from config, not hardcoded
4. **Conversation memory** — LLM sees recent messages for context continuity
5. **Graceful fallback** — Unknown queries get helpful "I'm not sure, but..." responses
6. **Confirmation for actions** — Booking/lead capture requires explicit confirmation
7. **Tool-based data retrieval** — Fetch business info via tools, not context stuffing (see below)

---

## Business Data Retrieval Strategy

### Decision: Tool/Function Calling with YAML Files (NOT Context Stuffing)

When the user asks about business information (hours, pricing, parking, services), how should the agent retrieve this data?

### Options Considered

| Approach | Description |
|----------|-------------|
| **Context Stuffing** | Inject ALL business info into system prompt |
| **Tool Calling** | Agent calls `get_business_info()` tool to fetch from YAML/JSON |
| **RAG/Vector Search** | Embed business data, semantic search |

### Recommendation: Tool Calling with Structured YAML Files

**Why NOT context stuffing:**
- Wastes ~1,500+ tokens per request even when user asks one simple question
- Hard to update (must redeploy prompts for every price change)
- Scales poorly for multi-business SaaS (linear token cost increase)
- Increases hallucination risk when data is embedded in prose

**Why NOT RAG/vector search:**
- Overkill for structured data (hours, prices are facts, not semantic)
- Added latency (100-300ms) and infrastructure complexity
- Accuracy risk: semantic search may return wrong price due to similarity

**Why tool calling wins:**

| Metric | Context Stuffing | Tool Calling |
|--------|------------------|--------------|
| Tokens per request | ~1,500+ | ~100-200 |
| Token savings | — | **~87%** |
| Update difficulty | High (redeploy) | Low (edit YAML) |
| Accuracy | Medium (hallucination) | Excellent (exact data) |
| Latency overhead | 0ms | ~100-150ms |
| Multi-business scale | Poor | Excellent |

### Implementation

**YAML Structure for Business Data:**
```yaml
business:
  id: "salon_123"
  name: "Luxe Salon"
  type: "hair_salon"

location:
  address: "123 Main St, Denver CO 80202"
  parking: "Free parking in rear lot, street parking available"
  landmarks: "Next to Starbucks on Main St"

hours:
  monday: { open: "09:00", close: "18:00" }
  tuesday: { open: "09:00", close: "18:00" }
  wednesday: { open: "09:00", close: "20:00" }  # Late night
  thursday: { open: "09:00", close: "18:00" }
  friday: { open: "09:00", close: "18:00" }
  saturday: { open: "10:00", close: "16:00" }
  sunday: { closed: true }

services:
  - id: "mens_haircut"
    name: "Men's Haircut"
    duration_minutes: 30
    price: 35
    description: "Classic cut with hot towel finish"
  - id: "womens_haircut"
    name: "Women's Haircut"
    duration_minutes: 45
    price: 55
    description: "Cut and style"
  - id: "color"
    name: "Full Color"
    duration_minutes: 120
    price: 120
    description: "Single-process color"

policies:
  cancellation: "Please cancel at least 24 hours in advance"
  deposit: "A $25 deposit is required for color services"
  walk_ins: "Walk-ins welcome, but appointments recommended"

faqs:
  - q: "Do you take walk-ins?"
    a: "Yes, walk-ins are welcome but appointments are recommended to guarantee your spot."
  - q: "What forms of payment do you accept?"
    a: "We accept cash, all major credit cards, and Apple Pay."
```

**Tool Definition:**
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
    # Load from YAML, return only requested data
    ...
```

**Agent Behavior:**
```
Customer: "What time do you close on Saturdays?"

LLM Decision: Call get_business_info(query_type="hours", specific_item="saturday")

Tool Returns: { "saturday": { "open": "10:00", "close": "16:00" } }

LLM Response: "We're open until 4 PM on Saturdays. Would you like to book an appointment?"
```

### When to Consider RAG (Future)

Add lightweight vector search ONLY if:
- FAQs grow beyond 30+ entries
- Policies become long prose documents (500+ chars)
- Users frequently ask interpretive/fuzzy questions

For MVP with ~50-200 structured data points per business, tool calling is sufficient and optimal

---

## Next Steps

1. Define tool schemas for all 6 core capabilities
2. Create system prompt template with business placeholders
3. Build simple backend with mock data (JSON files)
4. Test conversation flows for each capability
5. Add business configuration loader
6. Build basic chat UI widget
