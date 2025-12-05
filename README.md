# AI Receptionist

AI-powered chatbot for self-care businesses (salons, medspas, fitness studios, clinics). Embeddable chat widget that handles customer queries, appointment booking, and lead capture.

## Target Industries

- **Beauty:** Hair salons, barber shops, nail salons, makeup artists, brow & lash studios
- **Health & Wellness:** Medspas, wellness centers, chiropractic, massage, acupuncture
- **Medical & Specialty:** Plastic surgery, dermatology, dental, IV therapy, weight loss clinics
- **Fitness:** Boutique gyms, pilates, yoga, personal trainers, recovery studios

## Features

### Core (V1)
- Business info queries (hours, pricing, services, location, policies, FAQs)
- Embeddable chat widget with single `<script>` tag
- Admin panel for business setup and configuration
- Staff management
- Conversation context retention

### Booking & Lead Capture (V2)
- Appointment scheduling with calendar UI
- Lead capture and qualification
- Returning customer recognition
- Customer list management (CSV upload)
- SMS marketing (mock)

### Intelligence (V3)
- AI service recommendations
- Custom workflow builder (triggers + actions)
- Analytics dashboard
- Proactive follow-ups

### Business Intelligence (V4)
- Actionable insights (demand signals, scheduling optimization)
- Unanswered questions report
- Customer behavior analytics
- Revenue insights

## Tech Stack

- **Backend:** FastAPI + Agno AgentOS
- **Database:** SQLite
- **Frontend Widget:** Vanilla JS (embeddable)

## Project Structure

```
receptionist_ai/
├── agentic_development_docs/
│   ├── business_plan/          # Business idea and target market
│   └── project_design_plan/    # PRD and technical specs
└── README.md
```

## Documentation

- [PRD & Technical Spec](agentic_development_docs/project_design_plan/2_initial_plan.md)
- [Business Idea](agentic_development_docs/business_plan/0_keystone_business_idea.md)
- [Target Businesses](agentic_development_docs/business_plan/1_target_businesses_keystone.md)