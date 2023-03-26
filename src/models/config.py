from dataclasses import dataclass
from typing import Any, List, Mapping
from zoneinfo import ZoneInfo

from models.database import Database
from models.ical import ICalendar


@dataclass
class Config:
    databases: List[Database]
    icals: List[ICalendar]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        return cls(
            databases=[Database.from_dict(_) for _ in data["databases"]],
            icals=[ICalendar.from_dict(_) for _ in data["icals"]],
        )
