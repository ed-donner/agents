from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


DATA_FILE = Path(__file__).with_name("travel_data.json")


class Hotel(BaseModel):
    name: str
    destination: str
    area: str
    nightly_rate: float
    vibe: str
    highlights: list[str]


class Activity(BaseModel):
    name: str
    destination: str
    category: str
    area: str
    duration_hours: int
    price: float
    description: str


class ItineraryItem(BaseModel):
    day: int
    time: str
    title: str
    location: str
    cost: float
    notes: str


class Booking(BaseModel):
    type: str
    name: str
    destination: str
    total_cost: float
    details: str
    booked_at: str


class TravelerProfile(BaseModel):
    name: str
    destination: str
    days: int
    budget: float
    style: str
    interests: list[str]
    hotel_preferences: list[str]
    notes: str
    itinerary_title: str = ""
    itinerary_summary: str = ""
    itinerary_items: list[ItineraryItem] = Field(default_factory=list)
    bookings: list[Booking] = Field(default_factory=list)

    @classmethod
    def get(cls, name: str) -> "TravelerProfile":
        db = load_data()
        traveler = db["travelers"].get(name.lower())
        if not traveler:
            traveler = make_default_traveler(name).model_dump()
            db["travelers"][name.lower()] = traveler
            save_data(db)
        return cls(**traveler)

    def save(self) -> None:
        db = load_data()
        db["travelers"][self.name.lower()] = self.model_dump()
        save_data(db)

    def reset(self) -> None:
        fresh = make_default_traveler(self.name)
        self.destination = fresh.destination
        self.days = fresh.days
        self.budget = fresh.budget
        self.style = fresh.style
        self.interests = fresh.interests
        self.hotel_preferences = fresh.hotel_preferences
        self.notes = fresh.notes
        self.itinerary_title = ""
        self.itinerary_summary = ""
        self.itinerary_items = []
        self.bookings = []
        self.save()

    def profile_report(self) -> str:
        return json.dumps(
            {
                "name": self.name,
                "destination": self.destination,
                "days": self.days,
                "budget": self.budget,
                "style": self.style,
                "notes": self.notes,
            }
        )

    def preferences_report(self) -> str:
        return json.dumps(
            {
                "interests": self.interests,
                "hotel_preferences": self.hotel_preferences,
                "booking_count": len(self.bookings),
            }
        )

    def itinerary_report(self) -> str:
        return json.dumps(
            {
                "traveler": self.name,
                "title": self.itinerary_title,
                "summary": self.itinerary_summary,
                "items": [item.model_dump() for item in self.itinerary_items],
                "bookings": [booking.model_dump() for booking in self.bookings],
            }
        )

    def save_itinerary(self, title: str, summary: str) -> str:
        self.itinerary_title = title
        self.itinerary_summary = summary
        self.save()
        return f"Saved itinerary '{title}' for {self.name}."

    def add_itinerary_item(
        self,
        day: int,
        time: str,
        title: str,
        location: str,
        cost: float,
        notes: str,
    ) -> str:
        self.itinerary_items.append(
            ItineraryItem(
                day=day,
                time=time,
                title=title,
                location=location,
                cost=cost,
                notes=notes,
            )
        )
        self.itinerary_items.sort(key=lambda item: (item.day, item.time))
        self.save()
        return f"Added '{title}' on day {day} at {time}."

    def add_booking(
        self,
        booking_type: str,
        name: str,
        destination: str,
        total_cost: float,
        details: str,
    ) -> str:
        self.bookings.append(
            Booking(
                type=booking_type,
                name=name,
                destination=destination,
                total_cost=total_cost,
                details=details,
                booked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        self.save()
        return f"Booked {name} for {self.name}."


def default_catalog() -> dict:
    return {
        "lagos": {
            "hotels": [
                {
                    "name": "The Wheatbaker",
                    "destination": "Lagos",
                    "area": "Ikoyi",
                    "nightly_rate": 220.0,
                    "vibe": "quiet boutique luxury",
                    "highlights": ["art-filled lobby", "spa", "calm rooms"],
                },
                {
                    "name": "Nordic Hotel Lagos",
                    "destination": "Lagos",
                    "area": "Victoria Island",
                    "nightly_rate": 145.0,
                    "vibe": "minimal and peaceful",
                    "highlights": ["quiet rooms", "central location", "good breakfast"],
                },
                {
                    "name": "Radisson Blu Anchorage",
                    "destination": "Lagos",
                    "area": "Victoria Island",
                    "nightly_rate": 260.0,
                    "vibe": "waterfront business hotel",
                    "highlights": ["lagoon views", "pool", "easy restaurant access"],
                },
            ],
            "activities": [
                {
                    "name": "Nike Art Gallery Visit",
                    "destination": "Lagos",
                    "category": "art",
                    "area": "Lekki",
                    "duration_hours": 2,
                    "price": 0.0,
                    "description": "A large gallery with contemporary Nigerian art and textiles.",
                },
                {
                    "name": "Terra Kulture Evening Show",
                    "destination": "Lagos",
                    "category": "art",
                    "area": "Victoria Island",
                    "duration_hours": 3,
                    "price": 35.0,
                    "description": "A relaxed evening of theatre, live performance, and Nigerian cuisine.",
                },
                {
                    "name": "Sunset Dinner at Shiro",
                    "destination": "Lagos",
                    "category": "food",
                    "area": "Victoria Island",
                    "duration_hours": 2,
                    "price": 55.0,
                    "description": "A polished rooftop dinner with good ambience for a celebratory night.",
                },
                {
                    "name": "Breakfast at Art Cafe",
                    "destination": "Lagos",
                    "category": "food",
                    "area": "Victoria Island",
                    "duration_hours": 2,
                    "price": 18.0,
                    "description": "Casual breakfast spot with pastries, coffee, and a laid-back atmosphere.",
                },
                {
                    "name": "Lakowe Lakes Quiet Afternoon",
                    "destination": "Lagos",
                    "category": "relaxation",
                    "area": "Lekki Corridor",
                    "duration_hours": 5,
                    "price": 60.0,
                    "description": "A slower afternoon escape with open space, water views, and light activities.",
                },
                {
                    "name": "Spa Session at Oriki",
                    "destination": "Lagos",
                    "category": "wellness",
                    "area": "Victoria Island",
                    "duration_hours": 2,
                    "price": 40.0,
                    "description": "A wellness stop for a quiet reset during the trip.",
                },
            ],
        }
    }


def make_default_traveler(name: str) -> TravelerProfile:
    return TravelerProfile(
        name=name,
        destination="Lagos",
        days=3,
        budget=650.0,
        style="birthday staycation",
        interests=["art", "food", "quiet experiences"],
        hotel_preferences=["quiet hotel", "walkable area", "good breakfast"],
        notes="Prefer a moderate budget, calm evenings, and one memorable birthday dinner.",
    )


def load_data() -> dict:
    if not DATA_FILE.exists():
        data = {
            "travelers": {"yemi": make_default_traveler("Yemi").model_dump()},
            "catalog": default_catalog(),
        }
        save_data(data)
        return data
    return json.loads(DATA_FILE.read_text())


def save_data(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2))


def reset_traveler(name: str) -> TravelerProfile:
    traveler = TravelerProfile.get(name)
    traveler.reset()
    return traveler


def get_hotels(destination: str) -> list[Hotel]:
    db = load_data()
    city = db["catalog"].get(destination.lower(), {})
    return [Hotel(**hotel) for hotel in city.get("hotels", [])]


def get_activities(destination: str) -> list[Activity]:
    db = load_data()
    city = db["catalog"].get(destination.lower(), {})
    return [Activity(**activity) for activity in city.get("activities", [])]
