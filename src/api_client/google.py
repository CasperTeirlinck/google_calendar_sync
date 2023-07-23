import logging
from functools import partial
from pathlib import Path
from typing import Any, List, Mapping, Type

import pendulum as dt
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from src.models.database import Database
from src.models.event import CalendarEvent, ICalCalendarEvent, NotionCalendarEvent
from src.models.ical import ICalendar
from src.transformations.event_title import format_event_title
from src.transformations.google_to_calendar_event import (
    google_to_ical_calendar_event,
    google_to_notion_calendar_event,
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    # "https://www.googleapis.com/auth/tasks",
]
CREDENTIALS_PATH = Path(__file__).parents[2] / "config" / "secrets" / "google.json"


class GCalendar:
    """
    Google Calendar API client.
    """

    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            filename=CREDENTIALS_PATH,
            scopes=SCOPES,
        )
        self.calendar = build("calendar", "v3", credentials=self.credentials)

    def get_events_notion(
        self,
        database: Database,
        cutoff_days: int = 30,
    ) -> List[NotionCalendarEvent]:
        """
        Get all events in google calendar corresponsing to the given database.
        Only events from the past "cutoff_days" nr of days are retured.
        """

        logger.info("Getting all events from Google Calendar.")

        request = self.calendar.events().list(
            calendarId=database.calendar_id,
            sharedExtendedProperty=[
                f"{NotionCalendarEvent.notion_database_id_property_name}={database.id}",
            ],
            timeMin=dt.now().naive().subtract(days=cutoff_days).isoformat() + "Z",
            orderBy="startTime",
            singleEvents=True,
            maxResults=2500,
        )
        # TODO: pagination
        # TODO: implement incremental request with nextSyncToken

        response = request.execute().get("items", [])
        return list(
            filter(
                lambda _: _ is not None,
                map(
                    partial(google_to_notion_calendar_event, database=database),
                    response,
                ),
            )
        )

    def get_events_ical(
        self,
        icalendar: ICalendar,
        cutoff_days: int = 30,
    ) -> List[ICalCalendarEvent]:
        """
        Get all events in google calendar corresponsing to the given ical calendar.
        """

        logger.info("Getting all events from Google Calendar.")

        request = self.calendar.events().list(
            calendarId=icalendar.calendar_id,
            # NOTE: recurring root events seem to be retrieved regardless of timeMin, that is what we want.
            timeMin=dt.now().naive().subtract(days=cutoff_days).isoformat() + "Z",
            singleEvents=False,
            maxResults=2500,
        )

        response = request.execute().get("items", [])
        return list(
            filter(
                lambda _: _ is not None,
                map(
                    partial(google_to_ical_calendar_event, icalendar=icalendar),
                    response,
                ),
            )
        )

    def get_event_instances_ical(
        self,
        event_root: ICalCalendarEvent,
    ) -> List[ICalCalendarEvent]:
        """
        Get all individual instances of a recurring event.
        """

        logger.info(
            f"Getting recurring event instances for '{event_root.title}' from Google Calendar."
        )

        request = self.calendar.events().instances(
            calendarId=event_root.icalendar.calendar_id,
            eventId=event_root.google_event_id,
            maxResults=2500,
        )

        response = request.execute().get("items", [])
        return list(
            filter(
                lambda _: _ is not None,
                map(
                    partial(
                        google_to_ical_calendar_event, icalendar=event_root.icalendar
                    ),
                    response,
                ),
            )
        )

    def create_event_from_notion(self, event: NotionCalendarEvent) -> None:
        """
        Create a new event in Google Calendar.
        """

        request = self.calendar.events().insert(
            calendarId=event.database.calendar_id,
            body=self.event_to_request_body_notion(event),
        )

        request.execute()
        logger.info(f"Created event '{event.title}' in Google Calendar.")

    def create_event_from_ical(self, event: ICalCalendarEvent) -> str:
        """
        Create a new event in Google Calendar based on the ICal event.

        :return: The Google Calendar event id.
        """

        request = self.calendar.events().insert(
            calendarId=event.icalendar.calendar_id,
            body=self.event_to_request_body_ical(event),
        )

        response = request.execute()
        logger.info(f"Created event '{event.title}' in Google Calendar.")

        return response["id"]

    def update_event_from_notion(self, event: NotionCalendarEvent) -> None:
        """
        Update the given event in Google Calendar.
        """

        request = self.calendar.events().update(
            calendarId=event.database.calendar_id,
            eventId=event.google_event_id,
            body=self.event_to_request_body_notion(event),
        )

        request.execute()
        logger.info(f"Updating event '{event.title}' in Google Calendar.")

    def update_event_from_ical(self, event: ICalCalendarEvent) -> None:
        """
        Update the given event in Google Calendar based on the ICal event.
        """

        request = self.calendar.events().update(
            calendarId=event.icalendar.calendar_id,
            eventId=event.google_event_id,
            body=self.event_to_request_body_ical(event),
        )

        request.execute()
        logger.info(f"Updating event '{event.title}' in Google Calendar.")

    def delete_event_notion(self, event: NotionCalendarEvent) -> None:
        """
        Delete the given event from Google Calendar.
        """

        request = self.calendar.events().delete(
            calendarId=event.database.calendar_id,
            eventId=event.google_event_id,
        )

        request.execute()
        logger.info(f"Deleted event '{event.title}' from Google Calendar.")

    def delete_event_ical(self, event: ICalCalendarEvent) -> None:
        """
        Delete the given event from Google Calendar.
        """

        request = self.calendar.events().delete(
            calendarId=event.icalendar.calendar_id,
            eventId=event.google_event_id,
        )

        request.execute()
        logger.info(f"Deleted event '{event.title}' from Google Calendar.")

    def event_to_request_body(self, event: Type[CalendarEvent]) -> Mapping[str, Any]:
        """
        Parse calendar event object to json body for api requests.
        """

        return {
            "start": {
                "date": event.date.start.format("YYYY-MM-DD")
                if event.date.all_day
                else None,
                "dateTime": event.date.start.format("YYYY-MM-DDTHH:mm:ssZ")
                if not event.date.all_day
                else None,
                "timeZone": event.date.start.timezone_name
                if event.recurrence
                else None,
            },
            "end": {
                "date": event.date.end.format("YYYY-MM-DD")
                if event.date.all_day
                else None,
                "dateTime": event.date.end.format("YYYY-MM-DDTHH:mm:ssZ")
                if not event.date.all_day
                else None,
                "timeZone": event.date.end.timezone_name if event.recurrence else None,
            },
        }

    def event_to_request_body_notion(
        self, event: NotionCalendarEvent
    ) -> Mapping[str, Any]:
        """
        Parse calendar event object to json body for api requests.
        """

        return {
            **self.event_to_request_body(event),
            "summary": format_event_title(event),
            "description": f"<a href='{event.notion_page_url}'>Notion</a>",
            "source": {
                "title": event.title,
                "url": event.notion_page_url,
            },
            "extendedProperties": {
                "shared": {
                    NotionCalendarEvent.notion_database_id_property_name: event.database.id,
                    NotionCalendarEvent.notion_page_id_property_name: event.notion_page_id,
                    NotionCalendarEvent.notion_title_property_name: event.title,
                    NotionCalendarEvent.notion_icon_property_value_property_name: event.icon_property_value,
                }
            },
        }

    def event_to_request_body_ical(self, event: ICalCalendarEvent) -> Mapping[str, Any]:
        """
        Parse ical calendar event object to json body for api requests.
        """

        return {
            **self.event_to_request_body(event),
            "summary": event.title,
            "location": event.location,
            "status": event.status,
            **({"recurrence": [event.recurrence]} if event.recurrence else {}),
            **(
                {"recurringEventId": event.recurrence_id} if event.recurrence_id else {}
            ),
            **(
                {
                    "originalStartTime": {
                        "date": event.recurrence_start.format("YYYY-MM-DD")
                        if event.date.all_day
                        else None,
                        "dateTime": event.recurrence_start.format(
                            "YYYY-MM-DDTHH:mm:ssZ"
                        )
                        if not event.date.all_day
                        else None,
                        "timeZone": event.recurrence_start.timezone_name,
                    }
                }
                if event.recurrence_start
                else {}
            ),
            "extendedProperties": {
                "shared": {
                    ICalCalendarEvent.ical_uid_property_name: event.ical_uid,
                    **(
                        {
                            ICalCalendarEvent.ical_rrule_property_name: event.ical_rrule,
                        }
                        if event.ical_rrule
                        else {}
                    ),
                }
            },
        }

    def __del__(self):
        if self.calendar:
            self.calendar.close()
