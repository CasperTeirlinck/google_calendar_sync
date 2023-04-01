import copy
import logging

from models.ical import ICalendar
from api_client.google import GCalendar
from api_client.ical import ICal
from common.utils import is_older_than
from common.ical import (
    are_events_equivalent,
    get_recurring_exceptions,
    get_recurring_root,
    map_events,
    map_exceptions,
)

logger = logging.getLogger(__name__)


def sync_icalendar(ical: ICal, gcalendar: GCalendar, icalendar: ICalendar):
    """
    Sync an ical feed with Google Calendar.

    NOTE: Manually deleted instances of recurring events in google calendar in ical are not synced.
    """

    logger.info(f"Starting to sync icalendar {icalendar.name}.")

    # Get events from ICal and Google Calendar
    events_ical = ical.get_events(icalendar)
    events_google = gcalendar.get_events_ical(icalendar)

    # Map events from ICal to events from Google Calendar
    events_map = map_events(events_ical, events_google)

    # Create/Update/Delete events
    for events_ical, events_google in events_map:
        # Get root events & recurring exceptions
        event_root_ical = get_recurring_root(events_ical)
        event_exceptions_ical = get_recurring_exceptions(events_ical, event_root_ical)
        event_root_google = get_recurring_root(events_google)
        event_exceptions_google = get_recurring_exceptions(
            events_google, event_root_google
        )

        # Create root event
        if event_root_ical and not event_root_google:
            # Dont create new events that are older that 5 days
            if is_older_than(event_root_ical) and not event_root_ical.recurrence:
                continue

            id = gcalendar.create_event_from_ical(event_root_ical)
            event_root_google = copy.deepcopy(event_root_ical)
            event_root_google.google_event_id = id

        # Update root event
        if event_root_ical and event_root_google:
            if not are_events_equivalent(event_root_ical, event_root_google):
                event_root_ical.google_event_id = event_root_google.google_event_id
                gcalendar.update_event_from_ical(event_root_ical)

        # Delete root event
        if not event_root_ical and event_root_google:
            gcalendar.delete_event_ical(event_root_google)

        # Create/Reset recurring exceptions
        events_map_exceptions = map_exceptions(
            event_exceptions_ical, event_exceptions_google
        )
        event_instances_google = []
        for event_ical, event_google in events_map_exceptions:
            # Create new exception
            if event_ical and not event_google:
                if is_older_than(event_ical):
                    continue

                # Get matching instance from google calendar
                if not len(event_instances_google):
                    event_instances_google = gcalendar.get_event_instances_ical(
                        event_root_google
                    )
                event_google = [
                    event
                    for event in event_instances_google
                    if event.recurrence_start == event_ical.recurrence_start
                ]
                assert len(event_google) == 1
                event_google = event_google[0]

                # Update google instance with ical exception
                event_ical.google_event_id = event_google.google_event_id
                event_ical.recurrence_id = event_google.recurrence_id
                gcalendar.update_event_from_ical(event_ical)

            # Reset exception
            if not event_ical and event_google and event_root_ical:
                if is_older_than(event_google):
                    continue

                event_root_duration = (
                    event_root_google.date.end - event_root_google.date.start
                )
                event_google.date.end = (
                    event_google.recurrence_start + event_root_duration
                )
                event_google.date.start = event_google.recurrence_start
                event_google.date.all_day = event_root_google.date.all_day
                event_google.title = event_root_google.title
                event_google.location = event_root_google.location
                event_google.status = event_root_google.status

                gcalendar.update_event_from_ical(event_google)

    logger.info(f"Done syncing icalendar {icalendar.name}!")
