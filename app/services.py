from datetime import date, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models


class BookingConflictError(Exception):
    pass


def generate_slots(db: Session, staff_id: int, service_id: int, day: date):
    service = db.get(models.Service, service_id)
    if not service:
        raise ValueError("Service not found")

    weekday = day.weekday()
    rules = db.scalars(
        select(models.AvailabilityRule).where(
            and_(
                models.AvailabilityRule.staff_id == staff_id,
                models.AvailabilityRule.weekday == weekday,
                models.AvailabilityRule.is_active.is_(True),
            )
        )
    ).all()

    duration = timedelta(minutes=service.duration_minutes)
    slots = []

    for rule in rules:
        cursor = datetime.combine(day, rule.start_time)
        end_boundary = datetime.combine(day, rule.end_time)
        while cursor + duration <= end_boundary:
            occupied = db.scalar(
                select(models.Booking.id).where(
                    and_(
                        models.Booking.staff_id == staff_id,
                        models.Booking.start_time == cursor,
                        models.Booking.status == models.BookingStatus.booked,
                    )
                )
            )
            if not occupied:
                slots.append(cursor)
            cursor += duration

    return slots


def create_booking(db: Session, payload):
    service = db.get(models.Service, payload.service_id)
    if not service:
        raise ValueError("Service not found")

    end_time = payload.start_time + timedelta(minutes=service.duration_minutes)
    booking = models.Booking(
        business_id=payload.business_id,
        customer_id=payload.customer_id,
        staff_id=payload.staff_id,
        service_id=payload.service_id,
        start_time=payload.start_time,
        end_time=end_time,
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BookingConflictError("Selected slot already booked") from exc
    db.refresh(booking)
    return booking


def send_reminder(db: Session, booking_id: int, channel: str):
    booking = db.get(models.Booking, booking_id)
    if not booking:
        raise ValueError("Booking not found")

    customer = db.get(models.Customer, booking.customer_id)
    if not customer:
        raise ValueError("Customer not found")

    # Integrate Twilio/WhatsApp provider here.
    return {
        "booking_id": booking.id,
        "channel": channel,
        "recipient": customer.phone,
        "message": f"Reminder: your appointment starts at {booking.start_time.isoformat()}.",
        "status": "queued",
    }
