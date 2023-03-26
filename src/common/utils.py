from typing import List, Tuple, Type, Union

import pytz
from models.event import CalendarEvent, ICalCalendarEvent, NotionCalendarEvent
import datetime as dt


def get_event_by_page_id(
    events: List[CalendarEvent], notion_page_id: str
) -> CalendarEvent:
    """
    Get event by notion page id.
    """

    return next(
        (event for event in events if event.notion_page_id == notion_page_id),
        None,
    )


def get_events_by_ical_uid(
    events: List[ICalCalendarEvent], ical_uid: str
) -> ICalCalendarEvent:
    """
    Get event by ical uid.

    If multiple events exist with the same uid, this means there is a recurring event with an exception.
    In that case, explicitly return the original event.
    """

    return [event for event in events if event.ical_uid == ical_uid]


def are_events_equivalent_notion(
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


def are_events_equivalent_ical(
    event_ical: ICalCalendarEvent,
    event_google: ICalCalendarEvent,
) -> bool:
    """
    Assert if two events are functionally equivalent between ical and google calendar
    based on a subset of properties.
    """

    for property_ical, property_google in [
        (event_ical.date, event_google.date),
        (event_ical.title, event_google.title),
        (event_ical.location, event_google.location),
        (event_ical.status, event_google.status),
        (event_ical.ical_rrule, event_google.ical_rrule),
    ]:
        if property_ical != property_google:
            return False

    return True


def get_recurring_root_ical(
    events: List[ICalCalendarEvent],
) -> ICalCalendarEvent | None:
    """
    Get the root event from a list of events with the same ical uid.
    """

    if not len(events):
        return None

    # Validate
    assert len(set([event.ical_uid for event in events])) == 1

    # Get root event
    events_root = [event for event in events if not event.recurrence_start]
    assert len(events_root) == 1

    return events_root[0]


def get_recurring_exceptions_ical(
    events: List[ICalCalendarEvent], event_root: ICalCalendarEvent
) -> List[ICalCalendarEvent]:
    """
    Get the exceptions from a list of events with the same ical uid.
    """

    if not event_root:
        return []

    # Validate
    assert len(set([event.ical_uid for event in events])) == 1

    # Get the exceptions
    events_exceptions = [
        event
        for event in events
        if event.recurrence_start
        and (
            event.recurrence_start != event.date.start
            or event.title != event_root.title
            or event.location != event_root.location
            or event.status != event_root.status
            or (event.date.end - event.date.start)
            != (event_root.date.end - event_root.date.start)
        )
    ]

    return events_exceptions


def map_events_notion(
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


def map_events_ical(
    events_ical: List[ICalCalendarEvent],
    events_google: List[ICalCalendarEvent],
) -> List[Tuple[List[ICalCalendarEvent], List[ICalCalendarEvent]]]:
    """
    Map events from ICal to events from Google Calendar, based on the ical uid.
    If multiple events have the same uid, this means there is a recurring event with an exception.
    """

    events = []

    ids_ical = [_.ical_uid for _ in events_ical]
    ids_google = [_.ical_uid for _ in events_google]
    ids_all = set(ids_ical).union(ids_google)

    events.extend(
        [
            (
                get_events_by_ical_uid(events_ical, ical_uid),
                get_events_by_ical_uid(events_google, ical_uid),
            )
            for ical_uid in ids_all
        ]
    )

    return events


def map_exceptions_ical(
    event_exceptions_ical: List[ICalCalendarEvent],
    event_exceptions_google: List[ICalCalendarEvent],
) -> List[Tuple[ICalCalendarEvent, ICalCalendarEvent]]:
    """
    Map recurring event exceptions from ICal with Google Calendar, based on the dates.
    """

    events = []

    for event_ical in event_exceptions_ical:
        match = None
        for event_google in event_exceptions_google:
            if are_events_equivalent_ical(event_ical, event_google):
                match = event_google
                break
        events.append((event_ical, match))

    for event_google in event_exceptions_google:
        match = False
        for event_ical in event_exceptions_ical:
            if are_events_equivalent_ical(event_ical, event_google):
                match = True
                break
        if not match:
            events.append((None, event_google))

    return events


def get_timezone_name(date: Union[dt.date, dt.datetime]) -> str:
    """
    Return IANA timezone name from date or datetime object.
    """

    try:
        return date.tzinfo.zone
    except:
        pass
    try:
        return pytz.timezone(date.tzname()).zone
    except:
        pass
    return "UTC"


def is_older_than(event: Type[CalendarEvent], cutoff_days: int = 5) -> bool:
    """
    See if the given event is older that the cutoff
    """

    date = event.date.start
    if type(date) is dt.date:
        now = dt.date.today()
    if type(date) is dt.datetime:
        now = dt.datetime.today().replace(tzinfo=dt.timezone.utc)
    if date < now - dt.timedelta(days=cutoff_days):
        return True

    return False
