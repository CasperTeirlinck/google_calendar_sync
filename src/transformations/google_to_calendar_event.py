from typing import Mapping
import datetime as dt
import logging
from zoneinfo import ZoneInfo

from models.database import Database
from models.event import CalendarEvent, CalendarEventDate, ICalCalendarEvent
from models.ical import ICalendar

logger = logging.getLogger(__name__)


def event_to_calendar_event(event: Mapping, database: Database) -> CalendarEvent | None:
    """
    Parse json response of a google calendar event to a calendar event.
    TODO: notion caendar event model
    """

    # Get event data
    event_id = event["id"]
    event_date = event["start"].get("date")
    page_id = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(CalendarEvent.notion_page_id_property_name)
    )
    event_title = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(CalendarEvent.notion_title_property_name)
    )
    icon_property_value = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(CalendarEvent.notion_icon_property_value_property_name)
    )

    # Validation
    if not page_id:
        logger.warning(
            "An event from google calendar does not have the expected notion page property."
        )
        return None
    if not event_date:
        logger.warning(
            "An event from google calendar does not have the expected date format."
        )
        return None

    # Parse date
    try:
        event_date = dt.datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        logger.warning(
            "An event from google calendar does not have the expected date format."
        )
        return None

    # Create event
    return CalendarEvent(
        database=database,
        title=event_title,
        date=event_date,
        notion_page_id=page_id,
        google_event_id=event_id,
        icon_property_value=icon_property_value,
    )


def google_to_ical_calendar_event(
    event: Mapping, icalendar: ICalendar
) -> ICalCalendarEvent | None:
    """
    Parse json response of a google calendar event to an ical calendar event.
    """

    # Get event data
    event_id = event["id"]
    event_title = event["summary"]
    event_location = event.get("location")
    # --- event dates or datetimes
    event_time_start = event["start"].get("dateTime")
    event_time_end = event["end"].get("dateTime")
    event_date_start = event["start"].get("date")
    event_date_end = event["end"].get("date")
    event_tz_start = event["start"].get("timeZone")
    event_tz_end = event["end"].get("timeZone")
    event_date = None
    # --- original recurrence start date (for exceptions)
    event_time_rstart = event.get("originalStartTime", {}).get("dateTime")
    event_date_rstart = event.get("originalStartTime", {}).get("date")
    event_tz_rstart = event.get("originalStartTime", {}).get("timeZone")
    # --- recurrence rule
    event_rrule = event.get("recurrence", [None])[0]
    event_rid = event.get("recurringEventId")
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

    # Parse date: all-day event
    event_date = None
    if event_date_start:
        try:
            event_date = CalendarEventDate(
                dt.datetime.strptime(event_date_start, "%Y-%m-%d").date(),
                dt.datetime.strptime(event_date_end, "%Y-%m-%d").date(),
                all_day=True,
            )
        except ValueError:
            pass

    # Parse date: timed event
    if event_time_start:
        try:
            event_date = CalendarEventDate(
                dt.datetime.strptime(event_time_start, "%Y-%m-%dT%H:%M:%S%z"),
                dt.datetime.strptime(event_time_end, "%Y-%m-%dT%H:%M:%S%z"),
                all_day=False,
            )
        except ValueError:
            pass

    # Parse date: all-day event (recurrence exception)
    event_rstart = None
    if event_date_rstart:
        try:
            event_rstart = dt.datetime.strptime(event_date_rstart, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Parse date: timed event (recurrence exception)
    if event_time_rstart:
        try:
            event_rstart = dt.datetime.strptime(
                event_time_rstart, "%Y-%m-%dT%H:%M:%S%z"
            )
        except ValueError:
            pass

    if not event_date:
        logger.warning(
            "An event from google calendar does not have the expected date format."
        )
        return None

    # Timezones
    if event_tz_start:
        event_date.start = event_date.start.replace(tzinfo=ZoneInfo(event_tz_start))
    if event_tz_end:
        event_date.end = event_date.end.replace(tzinfo=ZoneInfo(event_tz_end))
    if event_tz_rstart:
        event_rstart = event_rstart.replace(tzinfo=ZoneInfo(event_tz_rstart))

    # Create event
    return ICalCalendarEvent(
        icalendar=icalendar,
        title=event_title,
        recurrence=event_rrule,
        recurrence_start=event_rstart,
        recurrence_id=event_rid,
        ical_rrule=ical_rrule,
        date=event_date,
        location=event_location,
        google_event_id=event_id,
        ical_uid=ical_uid,
    )
