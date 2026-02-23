from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Universal Appointment + Queue MVP")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/businesses")
def create_business(payload: schemas.BusinessCreate, db: Session = Depends(get_db)):
    item = models.Business(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/staff")
def create_staff(payload: schemas.StaffCreate, db: Session = Depends(get_db)):
    item = models.Staff(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/services")
def create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db)):
    item = models.Service(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/availability_rules")
def create_availability_rule(payload: schemas.AvailabilityRuleCreate, db: Session = Depends(get_db)):
    item = models.AvailabilityRule(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/customers")
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    item = models.Customer(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/slots")
def get_slots(staff_id: int, service_id: int, day: str, db: Session = Depends(get_db)):
    from datetime import date

    parsed_day = date.fromisoformat(day)
    slots = services.generate_slots(db, staff_id=staff_id, service_id=service_id, day=parsed_day)
    return {"slots": [slot.isoformat() for slot in slots]}


@app.post("/bookings", response_model=schemas.BookingOut)
def create_booking(payload: schemas.BookingCreate, db: Session = Depends(get_db)):
    try:
        return services.create_booking(db, payload)
    except services.BookingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/queue_events")
def create_queue_event(payload: schemas.QueueEventCreate, db: Session = Depends(get_db)):
    item = models.QueueEvent(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/reminders")
def send_reminder(payload: schemas.ReminderPayload, db: Session = Depends(get_db)):
    try:
        return services.send_reminder(db, payload.booking_id, payload.channel)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/queue/{business_id}", response_class=HTMLResponse)
def now_serving_page(business_id: int, db: Session = Depends(get_db)):
    business = db.get(models.Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    latest_now_serving = db.scalar(
        select(models.QueueEvent)
        .where(
            models.QueueEvent.business_id == business_id,
            models.QueueEvent.action == models.QueueAction.now_serving,
        )
        .order_by(models.QueueEvent.created_at.desc())
        .limit(1)
    )

    serving_label = "No one currently"
    if latest_now_serving:
        customer = db.get(models.Customer, latest_now_serving.customer_id)
        service = db.get(models.Service, latest_now_serving.service_id)
        serving_label = f"{customer.name} — {service.name}"

    return f"""
    <html>
      <head>
        <title>{business.name} Queue</title>
        <meta http-equiv="refresh" content="15">
        <style>
          body {{ font-family: Arial; max-width: 640px; margin: 2rem auto; }}
          .card {{ background: #f4f4f4; border-radius: 12px; padding: 1.5rem; }}
          h1 {{ margin-top: 0; }}
        </style>
      </head>
      <body>
        <div class="card">
          <h1>{business.name} — Now Serving</h1>
          <h2>{serving_label}</h2>
          <p>Auto refreshes every 15 seconds.</p>
        </div>
      </body>
    </html>
    """
