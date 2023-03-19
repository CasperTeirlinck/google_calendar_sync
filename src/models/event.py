from dataclasses import dataclass
import datetime as dt

from models.database import Database


@dataclass
class CalendarEvent:
    database: Database
    title: str
    date: dt.datetime
    notion_page_id: str
    notion_page_url: str = ""
    google_event_id: str = ""
    icon_property_value: str = ""

    # Extended properties keys on google calendar
    # reference: https://developers.google.com/calendar/api/guides/extended-properties
    notion_page_id_property_name: str = "NotionPageId"
    notion_database_id_property_name: str = "NotionDatabaseId"
    title_property_name: str = "NotionTitle"
    icon_property_value_property_name: str = "NotionIconPropertyValue"
