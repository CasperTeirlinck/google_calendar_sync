from dataclasses import dataclass
from typing import Any, Mapping


class WorkspaceName(str):
    pass


class DatabaseName(str):
    pass


@dataclass
class Database:
    """
    Notion database that maps to events in Google calendar.
    """

    # Notion workspace name. Should match the keys in the secrets file.
    workspace: WorkspaceName

    # Name is arbitrary but unique
    name: DatabaseName

    # Id is found in the url on Notion
    id: str

    # Corresponding Google Calendar id to sync to
    calendar_id: str

    # Name of the title property
    title_property: str

    # Name of the date property
    date_property: str

    # Notion property name used to determine icon in Google Calendar
    # this needs to be formatted as the full path to the property field depending on the property type
    # see https://developers.notion.com/reference/page-property-values for type specific paths
    # e.g. for a property named "State" of the type "status" use: `State/status/name` to use the name as icon identifier
    icon_property_path: str

    # Mapping from Notion property values to the icons used in Google Calendar
    icon_value_mapping: Mapping[str, str]

    # Default icon
    icon_default: str

    icon_property: str = None

    def __post_init__(self):
        self.icon_property = self.icon_property_path.split("/")[0]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]):
        return cls(
            workspace=WorkspaceName(data["workspace"]),
            name=DatabaseName(data["name"]),
            id=data["id"],
            calendar_id=data["calendar_id"],
            title_property=data["title_property"],
            date_property=data["date_property"],
            icon_property_path=data["icon_property_path"],
            icon_value_mapping=data["icon_value_mapping"],
            icon_default=data["icon_default"],
        )
