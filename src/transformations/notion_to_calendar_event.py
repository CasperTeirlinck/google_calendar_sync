from typing import Mapping
import pendulum as dt

from src.models.database import Database
from src.models.event import CalendarEventDate, NotionCalendarEvent


def page_to_calendar_event(page: Mapping, database: Database) -> NotionCalendarEvent:
    """
    Parse json config of a notion page to a calendar event.
    """

    # Get page data
    id = page["id"]
    url = page["url"]
    title = page["properties"][database.title_property]["title"][0]["plain_text"]
    date_start_string = page["properties"][database.date_property]["date"]["start"]
    date_end_string = page["properties"][database.date_property]["date"]["end"]

    icon_property_value = page["properties"][database.icon_property]
    for _ in database.icon_property_path.split("/")[1:]:
        icon_property_value = icon_property_value[_]

    # Parse date
    date = {
        "start": None,
        "end": None,
        "all_day": True,
    }
    for date_string, date_name in zip(
        [date_start_string, date_end_string],
        date.keys(),
    ):
        if not date_string:
            continue
        for date_format, all_day in zip(
            ["YYYY-MM-DD", "YYYY-MM-DDTHH:mm:ssZ", "YYYY-MM-DDTHH:mm:ss.SSSZ"],
            [True, False, False],
        ):
            try:
                date[date_name] = dt.from_format(date_string, date_format)
                date["all_day"] = all_day
                break
            except ValueError:
                continue
        if not date[date_name]:
            raise ValueError(
                f"Unrecognised date format for property {database.date_property}."
            )

    # Create event
    return NotionCalendarEvent(
        database=database,
        title=title,
        date=CalendarEventDate(**date),
        notion_page_id=id,
        notion_page_url=url,
        icon_property_value=icon_property_value,
    )
