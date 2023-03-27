from typing import Mapping, Optional, Union
import datetime as dt
import logging
import icalendar as ical

from models.database import Database
from models.event import CalendarEventDate, ICalCalendarEvent
from models.ical import ICalendar

logger = logging.getLogger(__name__)


def ical_to_calendar_event(
    event: ical.Event, icalendar: ICalendar
) -> ICalCalendarEvent | None:
    """
    Parse ical data of an event to a calendar event.
    """

    # Get event data
    ical_uid = str(event["UID"])
    event_title = str(event["SUMMARY"])
    event_status = str(event["STATUS"])
    event_location = str(event.get("LOCATION", ical.vText("")))
    event_start: Union[dt.date, dt.datetime] = event.get("DTSTART").dt
    event_end: Union[dt.date, dt.datetime] = event.get("DTEND").dt
    ical_rrule: Optional[ical.vRecur] = event.get("RRULE")
    ical_rid: Optional[ical.vDDDTypes] = event.get("RECURRENCE-ID")
    event_rrule = None

    # Parse date
    event_date = CalendarEventDate(start=event_start, end=event_end)

    # Parse recurrence
    if ical_rrule:
        ical_rrule: str = ical_rrule.to_ical().decode("utf-8")
        event_rrule = "RRULE:" + ical_rrule
    if ical_rid:
        ical_rid: Union[dt.date, dt.datetime] = ical_rid.dt

    # Parse location
    if not event_location.strip():
        event_location = None

    # Parse status
    ical_status_map = {
        "confirmed": "confirmed",
        "tentative": "tentative",
        "cancelled": "cancelled",
    }
    event_status = ical_status_map.get(event_status.lower())

    # Validation
    if not event_date:
        logger.warning("An event from ical does not have the expected date format.")
        return None
    if not event_status:
        logger.warning(
            "An event from ical has an unexpected value for the status property."
        )
        return None

    # Create event
    return ICalCalendarEvent(
        icalendar=icalendar,
        title=event_title,
        location=event_location,
        date=event_date,
        recurrence=event_rrule,
        recurrence_start=ical_rid,
        ical_rrule=ical_rrule,
        status=event_status,
        ical_uid=ical_uid,
    )
