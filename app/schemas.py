from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models import BookingStatus, QueueAction


class BusinessCreate(BaseModel):
    name: str
    timezone: str = "UTC"
    profile: str | None = None


class StaffCreate(BaseModel):
    business_id: int
    name: str


class ServiceCreate(BaseModel):
    business_id: int
    name: str
    duration_minutes: int = Field(gt=0)
    price: float | None = None


class AvailabilityRuleCreate(BaseModel):
    staff_id: int
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time


class CustomerCreate(BaseModel):
    business_id: int
    name: str
    phone: str


class SlotQuery(BaseModel):
    staff_id: int
    service_id: int
    day: date


class BookingCreate(BaseModel):
    business_id: int
    customer_id: int
    staff_id: int
    service_id: int
    start_time: datetime


class BookingOut(BaseModel):
    id: int
    business_id: int
    customer_id: int
    staff_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus

    class Config:
        from_attributes = True


class QueueEventCreate(BaseModel):
    business_id: int
    customer_id: int
    service_id: int
    action: QueueAction


class ReminderPayload(BaseModel):
    booking_id: int
    channel: str = "sms"
