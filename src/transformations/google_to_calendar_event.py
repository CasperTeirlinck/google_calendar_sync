from typing import Mapping, NamedTuple, Optional
import datetime as dt
import logging
from zoneinfo import ZoneInfo

from models.database import Database
from models.event import (
    CalendarEventDate,
    ICalCalendarEvent,
    NotionCalendarEvent,
)
from models.ical import ICalendar

logger = logging.getLogger(__name__)


class EventData(NamedTuple):
    id: str
    title: str
    location: Optional[str]
    date: CalendarEventDate


def parse_event(event: Mapping) -> EventData:
    """
    Parse json response of goole calendar event.
    """

    # General
    id = event["id"]
    title = event["summary"]
    location = event.get("location")

    # Dates
    time_start = event["start"].get("dateTime")
    time_end = event["end"].get("dateTime")
    date_start = event["start"].get("date")
    date_end = event["end"].get("date")
    tz_start = event["start"].get("timeZone")
    tz_end = event["end"].get("timeZone")
    date = None

    # Parse date: all-day event
    if date_start:
        try:
            date = CalendarEventDate(
                dt.datetime.strptime(date_start, "%Y-%m-%d").date(),
                dt.datetime.strptime(date_end, "%Y-%m-%d").date(),
            )
        except ValueError:
            pass

    # Parse date: timed event
    if time_start:
        try:
            date = CalendarEventDate(
                dt.datetime.strptime(time_start, "%Y-%m-%dT%H:%M:%S%z"),
                dt.datetime.strptime(time_end, "%Y-%m-%dT%H:%M:%S%z"),
            )
        except ValueError:
            pass

    if not date:
        logger.warning(
            "An event from google calendar does not have the expected date format."
        )
        return None

    return EventData(id=id, title=title, location=location, date=date)


def google_to_notion_calendar_event(
    event: Mapping, database: Database
) -> NotionCalendarEvent | None:
    """
    Parse json response of a google calendar event to a calendar event.
    """

    # Get event data
    event_data = parse_event(event)

    # Get Notion-specific data
    page_id = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(NotionCalendarEvent.notion_page_id_property_name)
    )
    event_title = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(NotionCalendarEvent.notion_title_property_name)
    )
    icon_property_value = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(NotionCalendarEvent.notion_icon_property_value_property_name)
    )

    # Validation
    if not page_id:
        logger.warning(
            "An event from google calendar does not have the expected notion page property."
        )
        return None

    # Create event
    return NotionCalendarEvent(
        database=database,
        title=event_title,
        date=event_data.date,
        notion_page_id=page_id,
        google_event_id=event_data.id,
        icon_property_value=icon_property_value,
    )


def google_to_ical_calendar_event(
    event: Mapping, icalendar: ICalendar
) -> ICalCalendarEvent | None:
    """
    Parse json response of a google calendar event to an ical calendar event.
    """

    # Get event data
    event_data = parse_event(event)

    # Get ICal-specific data
    recurring_time_start = event.get("originalStartTime", {}).get("dateTime")
    recurring_date_start = event.get("originalStartTime", {}).get("date")
    recurring_tz = event.get("originalStartTime", {}).get("timeZone")
    recurring_rule = event.get("recurrence", [None])[0]
    recurring_id = event.get("recurringEventId")
    ical_rrule = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(ICalCalendarEvent.ical_rrule_property_name)
    )
    ical_uid = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(ICalCalendarEvent.ical_uid_property_name)
    )

    # Validate
    if not ical_uid:
        return None

    # Parse recurring date: all-day event
    recurring_start = None
    if recurring_date_start:
        try:
            recurring_start = dt.datetime.strptime(
                recurring_date_start, "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    # Parse recurring date: timed event
    if recurring_time_start:
        try:
            recurring_start = dt.datetime.strptime(
                recurring_time_start, "%Y-%m-%dT%H:%M:%S%z"
            )
        except ValueError:
            pass

    # Timezones
    if recurring_tz:
        recurring_start = recurring_start.replace(tzinfo=ZoneInfo(recurring_tz))

    # Create event
    return ICalCalendarEvent(
        icalendar=icalendar,
        title=event_data.title,
        recurrence=recurring_rule,
        recurrence_start=recurring_start,
        recurrence_id=recurring_id,
        ical_rrule=ical_rrule,
        date=event_data.date,
        location=event_data.location,
        google_event_id=event_data.id,
        ical_uid=ical_uid,
    )
