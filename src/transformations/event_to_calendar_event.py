from typing import Mapping
import datetime as dt
import logging

from models.database import Database
from models.event import CalendarEvent

logger = logging.getLogger(__name__)


def event_to_calendar_event(event: Mapping, database: Database) -> CalendarEvent | None:
    """
    Parse json response of a google calendar event to a calendar event.
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
        .get(CalendarEvent.title_property_name)
    )
    icon_property_value = (
        event.get("extendedProperties", {})
        .get("shared", {})
        .get(CalendarEvent.icon_property_value_property_name)
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
