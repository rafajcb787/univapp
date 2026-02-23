# Universal Appointment + Queue System (MVP)

FastAPI MVP for clinics, salons, mechanics, government offices, and other service businesses.

## What is included

- Multi-business profile model (`businesses`, `staff`, `services`, `customers`).
- Availability rules and slot generation endpoint.
- Transaction-safe booking creation using DB unique constraint on `(staff_id, start_time)`.
- Queue events and a public **Now Serving** page (`/queue/{business_id}`).
- Reminder endpoint ready for Twilio SMS / WhatsApp Cloud API integration.

## Tech choices

- **Backend:** FastAPI + SQLAlchemy.
- **DB:** SQLite for local dev (swap to Postgres/Supabase in production).
- **Messaging:** pluggable stub currently returning queued payload.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

Open docs: `http://127.0.0.1:8000/docs`

## Core API flow

1. Create `business`, `staff`, `service`, `customer`.
2. Create weekly `availability_rules`.
3. Query `/slots?staff_id=...&service_id=...&day=YYYY-MM-DD`.
4. POST `/bookings` with selected start time.
5. POST `/queue_events` as customers join and move to `now_serving`.
6. Show public queue screen with `/queue/{business_id}`.
7. Trigger reminders with POST `/reminders`.

## Suggested next features

- Next.js web portal + React Native staff app.
- Role-based auth for business owners/staff.
- Payment/no-show deposits.
- Multi-location support.
- Google Calendar sync.
- Analytics dashboards (utilization, no-show rate, wait time).
