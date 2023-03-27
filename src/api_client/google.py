from functools import partial
from pathlib import Path
import datetime as dt
import logging
from typing import Any, List, Mapping, Type
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from models.database import Database
from models.event import CalendarEvent, ICalCalendarEvent, NotionCalendarEvent
from models.ical import ICalendar
from transformations.event_title import format_event_title
from transformations.google_to_calendar_event import (
    google_to_notion_calendar_event,
    google_to_ical_calendar_event,
)

logger = logging.getLogger(__name__)

# When modifying scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    # "https://www.googleapis.com/auth/tasks",
]


class GCalendar:
    """
    Google Calendar API client.

    Reference: https://developers.google.com/calendar/api/quickstart/python
    """

    def __init__(self):
        # Authentication
        self.credentials: Credentials | None = None
        self.calendar = None
        self.authenticate()

        # Google calendar api service
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

        # Create request
        time_min = dt.datetime.today() - dt.timedelta(days=cutoff_days)
        request = self.calendar.events().list(
            calendarId=database.calendar_id,
            sharedExtendedProperty=[
                f"{NotionCalendarEvent.notion_database_id_property_name}={database.id}",
            ],
            timeMin=time_min.isoformat() + "Z",
            orderBy="startTime",
            singleEvents=True,
            maxResults=2500,
        )
        # TODO: pagination
        # TODO: implement incremental request with nextSyncToken

        # Send request
        response = request.execute().get("items", [])

        # Parse into calendar events
        events = list(
            filter(
                lambda _: _ is not None,
                map(
                    partial(google_to_notion_calendar_event, database=database),
                    response,
                ),
            )
        )

        return events

    def get_events_ical(
        self,
        icalendar: ICalendar,
        cutoff_days: int = 30,
    ) -> List[ICalCalendarEvent]:
        """
        Get all events in google calendar corresponsing to the given ical calendar.
        """

        logger.info("Getting all events from Google Calendar.")

        # Create request
        time_min = dt.datetime.today() - dt.timedelta(days=cutoff_days)
        request = self.calendar.events().list(
            calendarId=icalendar.calendar_id,
            timeMin=time_min.isoformat()
            + "Z",  # NOTE: recurring root events seem to be retrieved regardless of timeMin, that is what we want.
            singleEvents=False,
            maxResults=2500,
        )

        # Send request
        response = request.execute().get("items", [])

        # Parse into calendar events
        events = list(
            filter(
                lambda _: _ is not None,
                map(
                    partial(google_to_ical_calendar_event, icalendar=icalendar),
                    response,
                ),
            )
        )

        return events

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

        # Send request
        response = request.execute().get("items", [])

        # Parse into calendar events
        events = list(
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

        return events

    def create_event_from_notion(self, event: NotionCalendarEvent) -> None:
        """
        Create a new event in Google Calendar.
        """

        # Create request
        request = self.calendar.events().insert(
            calendarId=event.database.calendar_id,
            body=self.event_to_request_body_notion(event),
        )

        # Send request
        request.execute()

        logger.info(f"Created event '{event.title}' in Google Calendar.")

    def create_event_from_ical(self, event: ICalCalendarEvent) -> str:
        """
        Create a new event in Google Calendar based on the ICal event.
        """

        # Create request
        request = self.calendar.events().insert(
            calendarId=event.icalendar.calendar_id,
            body=self.event_to_request_body_ical(event),
        )

        # Send request
        response = request.execute()
        logger.info(f"Created event '{event.title}' in Google Calendar.")

        event_id: str = response["id"]

        return event_id

    def update_event_from_notion(self, event: NotionCalendarEvent) -> None:
        """
        Update the given event in Google Calendar.
        """

        # Create request
        request = self.calendar.events().update(
            calendarId=event.database.calendar_id,
            eventId=event.google_event_id,
            body=self.event_to_request_body_notion(event),
        )

        # Send request
        request.execute()

        logger.info(f"Updating event '{event.title}' in Google Calendar.")

    def update_event_from_ical(self, event: ICalCalendarEvent) -> None:
        """
        Update the given event in Google Calendar based on the ICal event.
        """

        # Create request
        request = self.calendar.events().update(
            calendarId=event.icalendar.calendar_id,
            eventId=event.google_event_id,
            body=self.event_to_request_body_ical(event),
        )

        # Send request
        request.execute()

        logger.info(f"Updating event '{event.title}' in Google Calendar.")

    def delete_event_notion(self, event: NotionCalendarEvent) -> None:
        """
        Delete the given event from Google Calendar.
        """

        # Create request
        request = self.calendar.events().delete(
            calendarId=event.database.calendar_id,
            eventId=event.google_event_id,
        )

        # Send request
        request.execute()

        logger.info(f"Deleted event '{event.title}' from Google Calendar.")

    def delete_event_ical(self, event: ICalCalendarEvent) -> None:
        """
        Delete the given event from Google Calendar.
        """

        # Create request
        request = self.calendar.events().delete(
            calendarId=event.icalendar.calendar_id,
            eventId=event.google_event_id,
        )

        # Send request
        request.execute()

        logger.info(f"Deleted event '{event.title}' from Google Calendar.")

    def event_to_request_body(self, event: Type[CalendarEvent]) -> Mapping[str, Any]:
        """
        Parse calendar event object to json body for api requests.
        """

        return {
            "start": {
                "date": event.date.start.strftime("%Y-%m-%d")
                if event.date.all_day
                else None,
                "dateTime": event.date.start.strftime("%Y-%m-%dT%H:%M:%S%z")
                if not event.date.all_day
                else None,
                # "timeZone": get_timezone_name(event.date.start),
            },
            "end": {
                "date": event.date.end.strftime("%Y-%m-%d")
                if event.date.all_day
                else None,
                "dateTime": event.date.end.strftime("%Y-%m-%dT%H:%M:%S%z")
                if not event.date.all_day
                else None,
                # "timeZone": get_timezone_name(event.date.end),
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
                        "date": event.recurrence_start.strftime("%Y-%m-%d")
                        if event.date.all_day
                        else None,
                        "dateTime": event.recurrence_start.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"
                        )
                        if not event.date.all_day
                        else None,
                        # "timeZone": get_timezone_name(event.recurrence_start)
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

    def authenticate(self):
        """
        Use OAuth flow to generate credentials for the Google Calendar API.
        This will open the browser if new credentials need to be generated.

        BUG: Not working with Brave Browser.
        """

        secrets_path = Path(__file__).parents[2] / "config" / "secrets"
        token_path = str(secrets_path / "token.json")
        credentials_path = str(secrets_path / "credentials.json")

        # Get stored credentials
        creds = None
        if Path(secrets_path / "token.json").exists():
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Get new credentials
        if not creds or not creds.valid:
            # Refresh credentials
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            # Recreate credentials
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        self.credentials = creds

    def __del__(self):
        if self.calendar:
            self.calendar.close()
