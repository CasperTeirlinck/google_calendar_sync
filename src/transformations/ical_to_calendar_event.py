from typing import Optional
import pendulum as dt
import datetime
import logging
import icalendar as ical

from src.common.utils import to_datetime
from src.models.event import CalendarEventDate, ICalCalendarEvent
from src.models.ical import ICalendar

logger = logging.getLogger(__name__)


def ical_to_calendar_event(
    event: ical.Event, icalendar: ICalendar
) -> ICalCalendarEvent | None:
    """
    Parse ical data of an event to a calendar event.
    """

    # Get event data
    ical_uid = str(event["UID"])
    title = str(event["SUMMARY"])
    status = str(event["STATUS"])
    location = str(event.get("LOCATION", ical.vText("")))
    start: dt.DateTime = to_datetime(event.get("DTSTART").dt)
    end: dt.DateTime = to_datetime(event.get("DTEND").dt)
    all_day: bool = True if type(event.get("DTSTART").dt) is datetime.date else False
    ical_rrule: Optional[ical.vRecur] = event.get("RRULE")
    ical_rid: Optional[ical.vDDDTypes] = event.get("RECURRENCE-ID")
    rrule = None

    # Parse date
    event_date = CalendarEventDate(start, end, all_day)

    # Parse recurrence
    if ical_rrule:
        ical_rrule: str = ical_rrule.to_ical().decode("utf-8")
        rrule = "RRULE:" + ical_rrule
    if ical_rid:
        ical_rid: dt.DateTime = to_datetime(ical_rid.dt)

    # Ignore timezone for all-day events: recurence start can mismatch with start and end times if those contain no timezone data
    if all_day:
        start = start.set(tz="UTC")
        end = end.set(tz="UTC")
        if ical_rid:
            ical_rid = ical_rid.set(tz="UTC")

    # Parse location
    if not location.strip():
        location = None

    # Parse status
    ical_status_map = {
        "confirmed": "confirmed",
        "tentative": "tentative",
        "cancelled": "cancelled",
    }
    status = ical_status_map.get(status.lower())

    # Validation
    if not event_date:
        logger.warning("An event from ical does not have the expected date format.")
        return None
    if not status:
        logger.warning(
            "An event from ical has an unexpected value for the status property."
        )
        return None

    # Create event
    return ICalCalendarEvent(
        icalendar=icalendar,
        title=title,
        location=location,
        date=event_date,
        recurrence=rrule,
        recurrence_start=ical_rid,
        ical_rrule=ical_rrule,
        status=status,
        ical_uid=ical_uid,
    )
