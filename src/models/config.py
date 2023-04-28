from dataclasses import dataclass
from typing import Any, List, Mapping

from src.models.database import Database
from src.models.ical import ICalendar


@dataclass
class Config:
    databases: List[Database]
    icals: List[ICalendar]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        databases = data.get("databases", [])
        icals = data.get("icals", [])
        return cls(
            databases=[Database.from_dict(_) for _ in databases],
            icals=[ICalendar.from_dict(_) for _ in icals],
        )
