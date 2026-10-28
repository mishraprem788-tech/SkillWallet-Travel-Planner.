from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_INTERESTS = {
    "food",
    "culture",
    "nature",
    "adventure",
    "shopping",
    "nightlife",
    "history",
    "relaxation",
}

TravelStyle = Literal["budget", "mid-range", "luxury"]
Pace = Literal["relaxed", "moderate", "packed"]
GroupType = Literal["solo", "couple", "family", "friends"]


class TripRequest(BaseModel):
    destination: str = Field(..., min_length=2, max_length=120)
    start_date: date
    end_date: date
    budget: float = Field(..., gt=0, le=10_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    interests: list[str] = Field(..., min_length=1, max_length=8)
    travel_style: TravelStyle
    pace: Pace = "moderate"
    group_type: GroupType = "solo"
    travelers: int = Field(default=1, ge=1, le=12)

    @field_validator("destination")
    @classmethod
    def strip_destination(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Destination must be at least 2 characters.")
        return cleaned

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, values: list[str]) -> list[str]:
        unique: list[str] = []
        for item in values:
            key = item.strip().lower()
            if key not in ALLOWED_INTERESTS:
                raise ValueError(f"Unsupported interest: {item}")
            if key not in unique:
                unique.append(key)
        if not unique:
            raise ValueError("Select at least one interest.")
        return unique

    @model_validator(mode="after")
    def validate_dates(self) -> "TripRequest":
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after the start date.")
        nights = (self.end_date - self.start_date).days
        if nights > 13:
            raise ValueError("MVP supports trips of 14 days or fewer.")
        if self.start_date < date.today():
            raise ValueError("Start date cannot be in the past.")
        return self

    @property
    def days(self) -> int:
        return max(1, (self.end_date - self.start_date).days + 1)


class Activity(BaseModel):
    time_of_day: Literal["morning", "afternoon", "evening"]
    title: str
    description: str
    estimated_cost: float = Field(default=0, ge=0)
    location: str = ""


class DayPlan(BaseModel):
    day: int
    date: str
    theme: str
    activities: list[Activity]
    daily_budget: float = Field(default=0, ge=0)


class Itinerary(BaseModel):
    destination: str
    summary: str
    days: list[DayPlan]
    total_estimated_cost: float = Field(ge=0)
    currency: str
    tips: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    source: Literal["gemini", "demo"]
    saved: bool
    notices: list[str] = Field(default_factory=list)
    itinerary_id: str | None = None
    itinerary: Itinerary


class ServiceStatus(BaseModel):
    gemini_configured: bool
    supabase_configured: bool
    using_demo_fallback: bool
