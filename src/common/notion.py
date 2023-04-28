from typing import List, Tuple

from src.models.event import NotionCalendarEvent


def get_event_by_page_id(
    events: List[NotionCalendarEvent], notion_page_id: str
) -> NotionCalendarEvent:
    """
    Get event by notion page id.
    """

    return next(
        (event for event in events if event.notion_page_id == notion_page_id),
        None,
    )


def are_events_equivalent(
    event_notion: NotionCalendarEvent,
    event_google: NotionCalendarEvent,
) -> bool:
    """
    Assert if two events are functionally equivalent between notion and google calendar
    based on a subset of properties.
    """

    for property_notion, property_google in [
        (event_notion.date, event_google.date),
        (event_notion.title, event_google.title),
        (event_notion.icon_property_value, event_google.icon_property_value),
    ]:
        if property_notion != property_google:
            return False

    return True


def map_events(
    events_notion: List[NotionCalendarEvent],
    events_google: List[NotionCalendarEvent],
) -> List[Tuple[NotionCalendarEvent, NotionCalendarEvent]]:
    """
    Map events from Notion to events from Google Calendar.
    Based on the notion page id.
    """

    events = []

    page_ids_notion = [_.notion_page_id for _ in events_notion]
    page_ids_google = [_.notion_page_id for _ in events_google]
    page_ids_all = set(page_ids_notion).union(page_ids_google)

    events.extend(
        [
            (
                get_event_by_page_id(events_notion, notion_page_id),
                get_event_by_page_id(events_google, notion_page_id),
            )
            for notion_page_id in page_ids_all
        ]
    )

    return events
