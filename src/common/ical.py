from typing import List, Tuple

from src.models.event import ICalCalendarEvent


def get_events_by_ical_uid(
    events: List[ICalCalendarEvent], ical_uid: str
) -> ICalCalendarEvent:
    """
    Get event by ical uid.

    If multiple events exist with the same uid, this means there is a recurring event with an exception.
    In that case, explicitly return the original event.
    """

    return [event for event in events if event.ical_uid == ical_uid]


def are_events_equivalent(
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


def map_events(
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


def get_recurring_root(
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


def get_recurring_exceptions(
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


def map_exceptions(
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
            if are_events_equivalent(event_ical, event_google):
                match = event_google
                break
        events.append((event_ical, match))

    for event_google in event_exceptions_google:
        match = False
        for event_ical in event_exceptions_ical:
            if are_events_equivalent(event_ical, event_google):
                match = True
                break
        if not match:
            events.append((None, event_google))

    return events
