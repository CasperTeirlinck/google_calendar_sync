from dataclasses import dataclass
import pendulum as dt
from typing import Literal, Optional

from src.models.database import Database
from src.models.ical import ICalendar

DEFAULT_EVENT_DURATION_MIN = 30


@dataclass
class CalendarEventDate:
    start: dt.DateTime
    end: Optional[dt.DateTime] = None

    all_day: bool = True

    def __post_init__(self):
        # All day
        if self.all_day and not self.end:
            self.end = self.start.add(days=1)

        # Timed
        elif not self.all_day and not self.end:
            self.end = self.start.add(minutes=DEFAULT_EVENT_DURATION_MIN)


@dataclass
class CalendarEvent:
    title: str
    date: CalendarEventDate
    recurrence: Optional[str] = None
    recurrence_start: Optional[dt.DateTime] = None
    recurrence_id: Optional[str] = None
    google_event_id: str = ""


@dataclass(kw_only=True)
class NotionCalendarEvent(CalendarEvent):
    database: Database
    notion_page_id: str

    notion_page_url: str = ""
    icon_property_value: str = ""

    # Extended properties keys on google calendar
    # reference: https://developers.google.com/calendar/api/guides/extended-properties
    notion_title_property_name: str = "NotionTitle"
    notion_page_id_property_name: str = "NotionPageId"
    notion_database_id_property_name: str = "NotionDatabaseId"
    notion_icon_property_value_property_name: str = "NotionIconPropertyValue"


@dataclass(kw_only=True)
class ICalCalendarEvent(CalendarEvent):
    icalendar: ICalendar
    ical_uid: str

    location: Optional[str] = None
    status: Literal["confirmed", "tentative", "calcelled"] = "confirmed"

    # Recurrence rule indicates frequency of event
    ical_rrule: Optional[str] = None

    # Extended properties keys on google calendar
    # reference: https://developers.google.com/calendar/api/guides/extended-properties
    ical_uid_property_name: str = "ICalUID"
    ical_rrule_property_name: str = (
        "ICalRRULE"  # needed because google reorders the rrule string
    )
