from dataclasses import dataclass
import datetime as dt
from typing import Literal, Optional, Union

from models.database import Database
from models.ical import ICalendar

DEFAULT_EVENT_DURATION_MIN = 30


@dataclass
class CalendarEventDate:
    start: Union[dt.date, dt.datetime]
    end: Optional[Union[dt.date, dt.datetime]] = None

    all_day: bool = True

    def __post_init__(self):
        # All day
        if type(self.start) is dt.date:
            self.all_day = True

            if not self.end:
                self.end = self.start + dt.timedelta(days=1)

            # Timezone
            tz = dt.timezone.utc
            self.start = dt.datetime.combine(
                self.start, dt.datetime.min.time(), tzinfo=tz
            )
            self.end = dt.datetime.combine(self.end, dt.datetime.min.time(), tzinfo=tz)

        # Timed
        elif type(self.start) is dt.datetime:
            self.all_day = False

            if not self.end:
                self.end = self.start + dt.timedelta(minutes=DEFAULT_EVENT_DURATION_MIN)

            # Timezone
            tz_start = (
                dt.timezone(self.start.utcoffset())
                if self.start.utcoffset()
                else dt.timezone(dt.timedelta())
            )
            tz_end = (
                dt.timezone(self.end.utcoffset())
                if self.end.utcoffset()
                else dt.timezone(dt.timedelta())
            )
            self.start = self.start.astimezone(tz_start)
            self.end = self.end.astimezone(tz_end)


@dataclass
class CalendarEvent:
    title: str
    date: CalendarEventDate
    recurrence: Optional[str] = None
    recurrence_start: Optional[Union[dt.date, dt.datetime]] = None
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
