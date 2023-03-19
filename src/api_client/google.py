from functools import partial
from pathlib import Path
import os
import datetime as dt
import logging
from typing import Any, List, Mapping
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from models.database import Database
from models.event import CalendarEvent
from transformations.event_title import format_event_title
from transformations.event_to_calendar_event import event_to_calendar_event

logger = logging.getLogger(__name__)

# When modifying scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


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

    def get_events(
        self,
        database: Database,
        cutoff_days: int = 30,
    ) -> List[CalendarEvent]:
        """
        Get all events in google calendar corresponsing to the given database.
        Only events from the past "cutoff_days" nr of days are retured.
        """

        # Create request
        time_min = dt.datetime.today() - dt.timedelta(days=cutoff_days)
        request = self.calendar.events().list(
            calendarId=database.calendar_id,
            sharedExtendedProperty=[
                f"{CalendarEvent.notion_database_id_property_name}={database.id}",
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
                map(partial(event_to_calendar_event, database=database), response),
            )
        )

        return events

    def create_event(self, event: CalendarEvent) -> None:
        """
        Create a new event in Google Calendar.
        """

        # Create request
        request = self.calendar.events().insert(
            calendarId=event.database.calendar_id,
            body=self.event_to_request_body(event),
        )

        # Send request
        request.execute()

        logger.info(f"Created event '{event.title}' in Google Calendar.")

    def update_event(self, event: CalendarEvent) -> None:
        """
        Update the given event in Google Calendar.
        """

        # Create request
        request = self.calendar.events().update(
            calendarId=event.database.calendar_id,
            eventId=event.google_event_id,
            body=self.event_to_request_body(event),
        )

        # Send request
        request.execute()

        logger.info(f"Updating event '{event.title}' in Google Calendar.")

    def delete_event(self, event: CalendarEvent) -> None:
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

    def event_to_request_body(self, event: CalendarEvent) -> Mapping[str, Any]:
        """
        Parse calendar event object to json body for api requests.
        """

        return {
            "summary": format_event_title(event),
            "description": f"<a href='{event.notion_page_url}'>Notion</a>",
            "start": {
                "date": event.date.strftime("%Y-%m-%d"),
            },
            "end": {
                "date": (event.date + dt.timedelta(days=1)).strftime("%Y-%m-%d"),
            },
            "extendedProperties": {
                "shared": {
                    CalendarEvent.notion_database_id_property_name: event.database.id,
                    CalendarEvent.notion_page_id_property_name: event.notion_page_id,
                    CalendarEvent.title_property_name: event.title,
                    CalendarEvent.icon_property_value_property_name: event.icon_property_value,
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
