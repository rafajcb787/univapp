from datetime import date, datetime, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models, services
from app.database import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = TestingSessionLocal()

    business = models.Business(name="Test Clinic", timezone="UTC")
    db.add(business)
    db.flush()

    staff = models.Staff(business_id=business.id, name="Sam")
    service = models.Service(business_id=business.id, name="Consultation", duration_minutes=30)
    customer = models.Customer(business_id=business.id, name="Alex", phone="+123")
    db.add_all([staff, service, customer])
    db.flush()

    rule = models.AvailabilityRule(
        staff_id=staff.id,
        weekday=0,
        start_time=time(9, 0),
        end_time=time(11, 0),
        is_active=True,
    )
    db.add(rule)
    db.commit()

    yield db
    db.close()


def test_generate_slots_excludes_booked(db_session):
    monday = date(2026, 1, 5)
    payload = type(
        "P",
        (),
        {
            "business_id": 1,
            "customer_id": 1,
            "staff_id": 1,
            "service_id": 1,
            "start_time": datetime(2026, 1, 5, 9, 30),
        },
    )
    services.create_booking(db_session, payload)

    slots = services.generate_slots(db_session, staff_id=1, service_id=1, day=monday)
    values = [slot.strftime("%H:%M") for slot in slots]
    assert values == ["09:00", "10:00", "10:30"]


def test_create_booking_conflict(db_session):
    payload = type(
        "P",
        (),
        {
            "business_id": 1,
            "customer_id": 1,
            "staff_id": 1,
            "service_id": 1,
            "start_time": datetime(2026, 1, 5, 9, 0),
        },
    )

    services.create_booking(db_session, payload)
    with pytest.raises(services.BookingConflictError):
        services.create_booking(db_session, payload)
