from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class ICalendar:
    """
    A single external calendar that is subscribed to.
    """

    # Name is arbitrary but unique
    name: str

    # Icalendar .ics link
    url: str

    # Corresponding Google Calendar id to sync to
    calendar_id: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        return cls(
            name=data["name"],
            url=data["url"],
            calendar_id=data["calendar_id"],
        )
