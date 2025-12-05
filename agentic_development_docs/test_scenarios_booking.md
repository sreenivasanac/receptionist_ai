# AI Receptionist - Booking Flow Test Scenarios

Additional test scenarios focused on various booking edge cases and conversation flows.

**Business:** Sheela's Salon  
**Business ID:** `ba5935b9-03b8-4be7-9ca2-98bc2c7169d7`  
**Staff:** John, Sarah  

---

## Scenario 8: Time Preference Booking (Morning/Afternoon/Evening)

**Objective:** Test booking with time-of-day preferences instead of specific times.

### Conversation Flow

```
>>> Customer: Hi, I'd like to book a blowout sometime in the morning

Agent: Here are the morning time slots available for a Blowout:
- December 6th at 9:00 AM
- December 6th at 9:30 AM
- December 6th at 10:00 AM
- December 6th at 10:30 AM
- December 6th at 11:00 AM
...

Which time works best for you?

>>> Customer: 10am on Saturday would be perfect [slot:2025-12-06_10:00_any]

Agent: To complete your Blowout booking for December 6th at 10:00 AM, could you please provide:
- Your name
- Phone number

>>> Customer: Maria Garcia, 555-8001

Agent: Your Blowout appointment has been successfully booked for December 6, 2025, at 10:00 AM.
Confirmation #: BL10AM01
```

### Verification
```sql
SELECT customer_name, date, time, service_id
FROM appointments
WHERE customer_phone = '555-8001'
ORDER BY created_at DESC LIMIT 1;

-- Expected: Maria Garcia booked blowout on 2025-12-06 at 10:00
```

### Expected Result
- ✓ Morning slots filtered correctly (before 12 PM)
- ✓ Booking completed successfully

---

## Scenario 9: Rescheduling an Appointment

**Objective:** Customer reschedules an existing appointment to a new time.

### Conversation Flow

```
>>> Customer: Hi, I need to reschedule my appointment

Agent: I'd be happy to help you reschedule. Could you please provide the phone number 
associated with your appointment?

>>> Customer: My phone is 555-8001

Agent: I found your Blowout appointment on December 6, 2025, at 10:00 AM. 
When would you like to reschedule it to?

>>> Customer: Can I move it to next week, maybe Tuesday afternoon?

Agent: Here are the available afternoon slots for Tuesday, December 10th:
- 1:00 PM
- 1:30 PM
- 2:00 PM
- 2:30 PM
- 3:00 PM

Which time works for you?

>>> Customer: 2pm please [slot:2025-12-10_14:00_any]

Agent: Your Blowout appointment has been rescheduled from December 6th at 10:00 AM 
to December 10, 2025, at 2:00 PM.
New confirmation #: BL14PM02
```

### Verification
```sql
SELECT customer_name, date, time, status
FROM appointments
WHERE customer_phone = '555-8001'
ORDER BY created_at DESC LIMIT 2;

-- Expected: 
-- New appointment: 2025-12-10 at 14:00, status='scheduled'
-- Old appointment: 2025-12-06 at 10:00, status='cancelled' or rescheduled
```

### Expected Result
- ✓ Original appointment cancelled/marked as rescheduled
- ✓ New appointment created at requested time
- ✓ Same customer linked

---

## Scenario 10: Booking on a Closed Day (Sunday)

**Objective:** System should handle requests for closed days gracefully.

### Conversation Flow

```
>>> Customer: I want to book a manicure for this Sunday

Agent: I'm sorry, but Sheela's Salon is closed on Sundays. 

Our hours are:
- Monday: 10:05 AM - 7:00 PM
- Tuesday-Friday: 9:00 AM - 7:00 PM (8:00 PM on Thu/Fri)
- Saturday: 9:00 AM - 6:00 PM

Would you like to book on Saturday or another day instead?

>>> Customer: Saturday works then

Agent: Here are the available times for a Manicure on Saturday:
- 9:00 AM
- 9:30 AM
- 10:00 AM
...

>>> Customer: 11am is good [slot:2025-12-07_11:00_any]

Agent: Please provide your name and phone number to complete the booking.

>>> Customer: Tom Chen, 555-8002

Agent: Your Manicure appointment has been booked for Saturday, December 7, 2025, at 11:00 AM.
Confirmation #: MAN11AM
```

### Verification
- ✓ System rejects Sunday booking
- ✓ Offers alternative days
- ✓ Booking completed on valid day

---

## Scenario 11: FAQ and Policy Questions Before Booking

**Objective:** Customer asks about policies before deciding to book.

### Conversation Flow

```
>>> Customer: Do you have a cancellation policy?

Agent: Yes, we require 24 hours notice for cancellations. If you need to cancel or reschedule, 
please let us know at least 24 hours in advance.

>>> Customer: Do I need to pay a deposit?

Agent: No, we don't require a deposit for appointments. You'll pay at the time of your service.

>>> Customer: What payment methods do you accept?

Agent: We accept cash, all major credit cards (Visa, Mastercard, Amex), and Apple Pay.

>>> Customer: Great! Can I book a pedicure for Friday evening?

Agent: Here are the evening slots available for a Pedicure on Friday:
- 5:00 PM
- 5:30 PM
- 6:00 PM
- 6:30 PM
- 7:00 PM

Which time works for you?

>>> Customer: 6pm [slot:2025-12-06_18:00_any]

Agent: Please provide your name and phone number.

>>> Customer: Diana Ross, 555-8003

Agent: Your Pedicure appointment has been booked for Friday, December 6, 2025, at 6:00 PM.
Confirmation #: PED6PM
```

### Verification
- ✓ Policy questions answered correctly
- ✓ Booking flow initiated after Q&A
- ✓ Appointment created

---

## Scenario 12: Booking Long Duration Service (Balayage - 3 hours)

**Objective:** Book a long service and verify duration is considered for slot availability.

### Conversation Flow

```
>>> Customer: I want to book a balayage. How long does it take?

Agent: A Balayage service takes approximately 180 minutes (3 hours) and costs $200. 
It's a hand-painted highlighting technique that creates a natural, sun-kissed look.

Would you like me to check available times?

>>> Customer: Yes please, what do you have next week?

Agent: Here are the available times for Balayage next week:
- Monday, Dec 9th at 10:05 AM (ends ~1:05 PM)
- Monday, Dec 9th at 2:00 PM (ends ~5:00 PM)
- Tuesday, Dec 10th at 9:00 AM (ends ~12:00 PM)
- Tuesday, Dec 10th at 1:00 PM (ends ~4:00 PM)
...

>>> Customer: Tuesday morning works [slot:2025-12-10_09:00_any]

Agent: Please provide your contact information.

>>> Customer: Sophie Turner, 555-8004, sophie@email.com

Agent: Your Balayage appointment has been booked for Tuesday, December 10, 2025, at 9:00 AM.
Please allow approximately 3 hours for this service.
Confirmation #: BAL9AM
```

### Verification
```sql
SELECT customer_name, date, time, duration_minutes, service_id
FROM appointments
WHERE customer_phone = '555-8004';

-- Expected: duration_minutes = 180
```

### Expected Result
- ✓ Duration mentioned to customer
- ✓ Correct duration stored in appointment
- ✓ Slot blocked for full 3 hours

---

## Scenario 13: Multiple Services Inquiry (Not Same Appointment)

**Objective:** Customer asks about multiple services but books just one.

### Conversation Flow

```
>>> Customer: What's the difference between a manicure and gel nails?

Agent: Great question! Here's the difference:

**Manicure** ($30, 30 min):
- Traditional nail care including shaping, cuticle care, and regular polish
- Polish typically lasts 5-7 days

**Gel Nails** ($50, 60 min):
- Same nail care plus gel polish that's cured under UV/LED light
- Lasts 2-3 weeks without chipping
- More durable and shiny finish

Would you like to book either service?

>>> Customer: I'll go with gel nails since they last longer

Agent: Great choice! Here are the available times for Gel Nails:
- December 6th at 9:00 AM
- December 6th at 10:00 AM
- December 6th at 11:00 AM
...

>>> Customer: Saturday at 2pm if available [slot:2025-12-07_14:00_any]

Agent: Please provide your name and phone number.

>>> Customer: Nicole Adams, 555-8005

Agent: Your Gel Nails appointment has been booked for Saturday, December 7, 2025, at 2:00 PM.
Confirmation #: GEL2PM
```

### Verification
- ✓ Both services explained
- ✓ Single service booked
- ✓ Correct service_id in database

---

## Scenario 14: Walk-in Availability Check (Same Day)

**Objective:** Customer checks if walk-ins are available today.

### Conversation Flow

```
>>> Customer: Do you take walk-ins? I need a quick haircut today

Agent: Yes, walk-ins are welcome at Sheela's Salon! However, appointments are recommended 
to guarantee your preferred time.

Let me check today's availability for a haircut. What type of haircut do you need?
- Women's Haircut ($60, 45 min)
- Men's Haircut ($35, 30 min)  
- Kids Haircut ($25, 20 min)

>>> Customer: Men's haircut

Agent: Here are the available slots for today:
- 3:00 PM with John
- 3:30 PM with John
- 4:00 PM with Sarah
- 4:30 PM with Sarah
...

Would you like to book one of these slots, or you can also walk in and we'll try to fit you in!

>>> Customer: I'll book 3pm to be safe [slot:2025-12-05_15:00_6367c482-325f-40e6-bff0-27988a9b90f3]

Agent: Please provide your name and phone.

>>> Customer: Mike Johnson, 555-8006

Agent: Your Men's Haircut appointment has been booked for today at 3:00 PM with John.
Confirmation #: MEN3PM
```

### Verification
- ✓ Walk-in policy communicated
- ✓ Same-day availability shown
- ✓ Booking completed

---

## Scenario 15: Price-Conscious Customer (Budget Questions)

**Objective:** Customer asks about prices and chooses based on budget.

### Conversation Flow

```
>>> Customer: What's your cheapest hair service?

Agent: Our most affordable hair services are:
- **Brow Wax** - $18 (15 min)
- **Kids Haircut** - $25 (20 min)
- **Men's Haircut** - $35 (30 min)
- **Blowout** - $45 (45 min)

For a full haircut with styling, our Women's Haircut is $60.

What are you looking for?

>>> Customer: How much for color services?

Agent: Here are our color services:
- **Full Color** - $120 (2 hours)
- **Highlights** - $150 (2.5 hours)
- **Balayage** - $200 (3 hours)

The Full Color is our most affordable option for a complete color change.

>>> Customer: I'll do the full color. What times do you have?

Agent: Here are the available times for Full Color:
- December 6th at 9:00 AM
- December 6th at 11:30 AM
- December 9th at 10:05 AM
...

>>> Customer: Monday morning [slot:2025-12-09_10:05_any]

Agent: Please provide your contact details.

>>> Customer: Kelly White, 555-8007

Agent: Your Full Color appointment has been booked for Monday, December 9, 2025, at 10:05 AM.
Total: $120 | Duration: ~2 hours
Confirmation #: CLR1005
```

### Verification
- ✓ Price information provided
- ✓ Budget-friendly options highlighted
- ✓ Correct service booked

---

## Scenario 16: Bridal/Special Event Inquiry (Lead + Booking)

**Objective:** Bridal inquiry triggers both lead capture and potential booking.

### Conversation Flow

```
>>> Customer: I'm getting married in March and need hair and makeup for my bridal party

Agent: Congratulations on your upcoming wedding! We'd love to help make your special day beautiful.

For bridal parties, we typically recommend a consultation first to discuss your vision and 
the services needed for you and your bridal party.

Could you tell me:
- How many people are in your bridal party?
- What date is your wedding?

>>> Customer: 6 people including me. Wedding is March 15th

Agent: Thank you! For a bridal party of 6, I'll capture your details so our bridal specialist 
can reach out to discuss packages and pricing.

Could you provide your name, email, and phone number?

>>> Customer: Emily Stone, emily.stone@email.com, 555-8008

Agent: Thank you, Emily! Your bridal inquiry has been captured. Our team will contact you 
within 24-48 hours to discuss bridal packages for your March 15th wedding.

In the meantime, would you like to book a consultation appointment to discuss your vision?

>>> Customer: Yes, that would be great

Agent: Here are available consultation times:
- December 9th at 11:00 AM
- December 10th at 2:00 PM
- December 11th at 10:00 AM
...

>>> Customer: December 10th at 2pm works [slot:2025-12-10_14:00_any]

Agent: Your bridal consultation has been booked for December 10, 2025, at 2:00 PM.
We look forward to helping you plan your perfect bridal look!
Confirmation #: BRIDAL01
```

### Verification
```sql
-- Check lead capture
SELECT name, email, interest, notes
FROM leads
WHERE phone = '555-8008';

-- Expected: Interest contains 'bridal' or 'wedding'

-- Check appointment
SELECT customer_name, date, service_id, notes
FROM appointments
WHERE customer_phone = '555-8008';

-- Expected: Consultation booked
```

### Expected Result
- ✓ Lead captured with bridal interest
- ✓ Consultation appointment booked
- ✓ Special event details noted

---

## Scenario 17: Service Not Offered

**Objective:** Customer asks for a service the salon doesn't offer.

### Conversation Flow

```
>>> Customer: Do you do massage therapy?

Agent: I'm sorry, but we don't currently offer massage therapy at Sheela's Salon. 
We specialize in hair, nail, and beauty services.

Our services include:
- Hair: Cuts, Color, Highlights, Balayage, Blowouts
- Nails: Manicure, Pedicure, Gel Nails
- Beauty: Brow Wax, Lash Extensions

Is there anything else I can help you with?

>>> Customer: What about facials?

Agent: We don't offer facials at this time. However, our Lash Extensions service ($150, 90 min) 
includes a relaxing eye treatment.

Would you like to book any of our available services?

>>> Customer: I'll try the lash extensions then

Agent: Great choice! Here are available times for Lash Extensions:
- December 6th at 9:00 AM
- December 6th at 10:30 AM
- December 9th at 10:05 AM
...

>>> Customer: Saturday morning [slot:2025-12-07_09:00_any]

Agent: Please provide your name and phone number.

>>> Customer: Julia Roberts, 555-8009

Agent: Your Lash Extensions appointment has been booked for Saturday, December 7, 2025, at 9:00 AM.
Duration: 90 minutes | Price: $150
Confirmation #: LASH9AM
```

### Verification
- ✓ Politely declines unavailable service
- ✓ Suggests alternatives
- ✓ Books available service

---

## Test Results Summary

| # | Scenario | Focus Area | Expected Outcome |
|---|----------|------------|------------------|
| 8 | Time Preference | Morning/afternoon filtering | Correct time slots shown |
| 9 | Rescheduling | Change existing appointment | Old cancelled, new created |
| 10 | Closed Day | Sunday booking attempt | Redirected to valid day |
| 11 | FAQ Before Booking | Policy questions | Info provided, then booking |
| 12 | Long Service | 3-hour balayage | Duration tracked correctly |
| 13 | Service Comparison | Manicure vs Gel | Education then booking |
| 14 | Walk-in Check | Same day availability | Policy + available slots |
| 15 | Budget Questions | Price-focused customer | Affordable options shown |
| 16 | Bridal Inquiry | Special event | Lead + consultation booking |
| 17 | Service Not Offered | Massage request | Polite decline, alternatives |

---

## API Testing Template

```bash
#!/bin/bash
BUSINESS_ID="ba5935b9-03b8-4be7-9ca2-98bc2c7169d7"
BASE_URL="http://localhost:8001"
SESSION_ID="test_$(date +%s)"

# Clear session
curl -s -X DELETE "$BASE_URL/chat/session/$BUSINESS_ID/$SESSION_ID"

# Send message function
send_message() {
    curl -s -X POST "$BASE_URL/chat/message" \
      -H "Content-Type: application/json" \
      -d "{
        \"business_id\": \"$BUSINESS_ID\",
        \"session_id\": \"$SESSION_ID\",
        \"message\": \"$1\"
      }" | python3 -c "import json,sys; d=json.load(sys.stdin); print('Agent:', d['message'][:300])"
}

# Example usage:
send_message "I want to book a blowout for tomorrow morning"
```

---

## Database Verification Queries

```sql
-- Check all test bookings
SELECT customer_name, customer_phone, service_id, date, time, status
FROM appointments
WHERE customer_phone LIKE '555-800%'
ORDER BY created_at DESC;

-- Check leads from special inquiries
SELECT name, email, phone, interest, company
FROM leads
WHERE phone LIKE '555-800%'
ORDER BY created_at DESC;

-- Check customer records created
SELECT first_name, last_name, phone, visit_count
FROM customers
WHERE phone LIKE '555-800%'
ORDER BY created_at DESC;
```
