from dataclasses import dataclass
from typing import Any, List, Mapping

from models.database import Database


@dataclass
class Config:
    databases: List[Database]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        return cls(databases=[Database.from_dict(_) for _ in data["databases"]])
