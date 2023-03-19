from typing import Mapping
import datetime as dt

from models.database import Database
from models.event import CalendarEvent


def page_to_calendar_event(page: Mapping, database: Database) -> CalendarEvent:
    """
    Parse json config of a notion page to a calendar event.
    """

    # Get page data
    page_id = page["id"]
    page_url = page["url"]
    page_title = page["properties"][database.title_property]["title"][0]["plain_text"]
    page_date_string = page["properties"][database.date_property]["date"]["start"]

    icon_property_value = page["properties"][database.icon_property]
    for _ in database.icon_property_path.split("/")[1:]:
        icon_property_value = icon_property_value[_]

    # Parse date
    page_date = None
    for date_format in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"]:
        try:
            page_date = dt.datetime.strptime(page_date_string, date_format)
            break
        except ValueError:
            continue
    if not page_date:
        raise ValueError(
            f"Unrecognised date format for property {database.date_property}."
        )

    # Create event
    return CalendarEvent(
        database=database,
        title=page_title,
        date=page_date,
        notion_page_id=page_id,
        notion_page_url=page_url,
        icon_property_value=icon_property_value,
    )
