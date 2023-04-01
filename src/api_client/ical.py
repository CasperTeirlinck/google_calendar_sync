from functools import partial
import logging
from typing import List
import icalendar as ical
import pendulum as dt
import requests
from common.utils import to_datetime

from models.event import ICalCalendarEvent
from models.ical import ICalendar
from transformations.ical_to_calendar_event import ical_to_calendar_event

logger = logging.getLogger(__name__)


class ICal:
    """
    ICalendar client.

    Interfaces with a simple .ics link to get information from arbitrary shared calendars.
    """

    def __init__(self) -> None:
        pass

    def get_events(
        self,
        icalendar: ICalendar,
        cutoff_days: int = 30,
    ) -> List[ICalCalendarEvent]:
        """
        Get all events in google calendar corresponsing to the given database.
        Only events from the past "cutoff_days" nr of days are retured.
        Only events from of "extend_days" nre of days in the future are retured.
        """

        logger.info("Getting all events from ICal.")

        # Get request
        response = requests.get(icalendar.url)

        # Parse ical content
        calendar: ical.Calendar = ical.Calendar.from_ical(response.content)
        events: List[ical.Event] = []
        for item in calendar.walk():
            if item.name == "VEVENT":
                event = ical.Event.from_ical(item.to_ical())

                # Filter on date
                date = to_datetime(event.get("DTSTART").dt)
                time_min = dt.now().subtract(days=cutoff_days)
                if date < time_min and not event.get("RRULE"):
                    continue

                events.append(event)

        # Parse into calendar events
        events = list(
            filter(
                lambda _: _ is not None,
                map(partial(ical_to_calendar_event, icalendar=icalendar), events),
            )
        )

        return events
