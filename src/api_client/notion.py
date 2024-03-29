import json
import logging
import urllib.parse
from functools import partial
from itertools import takewhile
from pathlib import Path
from typing import Any, Iterator, List, Mapping, Optional

import pendulum as dt
import requests

from src.models.database import Database, DatabaseName, WorkspaceName
from src.models.event import CalendarEvent, NotionCalendarEvent
from src.transformations.notion_to_calendar_event import page_to_calendar_event

logger = logging.getLogger(__name__)

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
CREDENTIALS_PATH = Path(__file__).parents[2] / "config" / "secrets" / "notion.json"


class Notion:
    """
    Notion HTTP api client

    Reference: https://developers.notion.com/reference/intro
    Versioning: https://developers.notion.com/reference/changes-by-version
    """

    def __init__(self):
        self.base_url = BASE_URL.rstrip("/")
        self.version = NOTION_VERSION

        self.auth_headers: Mapping[WorkspaceName, Mapping[str, str]]
        self.init_integration_tokens_per_workspace()

        self.database_objects: Mapping[DatabaseName, Mapping] = {}

    def init_integration_tokens_per_workspace(self):
        """
        Read and store integration tokens per workspace.
        """

        with open(CREDENTIALS_PATH, "r") as f:
            secrets = json.load(f)
        tokens: Mapping[WorkspaceName, str] = secrets["integration_tokens"]
        self.auth_headers: Mapping[WorkspaceName, Mapping[str, str]] = {
            workspace: {
                "Authorization": f"Bearer {token}",
                "Notion-Version": self.version,
                "accept": "application/json",
            }
            for workspace, token in tokens.items()
        }

    def get(self, path: str, database: Database) -> Mapping:
        """
        Authorised GET request.
        """

        try:
            auth_headers = self.auth_headers[database.workspace]
        except KeyError:
            raise Exception(
                f"Workspace {database.workspace} does not have an integration token configured."
            )

        response = requests.get(
            f"{self.base_url}/{path.lstrip('/')}",
            headers=auth_headers,
        )

        if not 200 <= response.status_code <= 299:
            raise Exception(f"Get request failed: {response.text}.")

        return response.json()

    def post(
        self,
        path: str,
        body: Mapping[str, Any],
        database: Database,
        query: Optional[Mapping[str, Any]] = None,
    ) -> Mapping:
        """
        Authorised POST request.
        """

        try:
            auth_headers = self.auth_headers[database.workspace]
        except KeyError:
            raise Exception(
                f"Workspace {database.workspace} does not have an integration token configured."
            )

        response = requests.post(
            f"{self.base_url}/{path.lstrip('/')}",
            json=body,
            params=query,
            headers={
                **auth_headers,
                "content-type": "application/json",
            },
        )

        if not 200 <= response.status_code <= 299:
            raise Exception(f"Post request failed: {response.text}.")

        return response.json()

    def post_paginated(
        self,
        path: str,
        body: Mapping[str, Any],
        database: Database,
        query: Optional[Mapping[str, Any]] = None,
        start_cursor: Optional[str] = None,
    ) -> Iterator[Any]:
        """
        Post request with recursive pagination.
        """

        body = {
            **body,
            **({"start_cursor": start_cursor} if start_cursor else {}),
            "page_size": 100,
        }

        response = self.post(path, body, database, query)

        next_cursor = response.get("next_cursor")
        if next_cursor:
            logger.info(f"Performing recursive paginated request")
            yield from self.post_paginated(path, body, database, query, next_cursor)

        yield from response["results"]

    def get_database(self, database: Database, ignore_cache: bool = False) -> Mapping:
        """
        Get database object and cache it.
        """

        if database.name in self.database_objects.keys() and not ignore_cache:
            return self.database_objects[database.name]

        response = self.get(f"databases/{database.id}", database)
        self.database_objects[database.name] = response

        return response

    def get_events(
        self,
        database: Database,
        cutoff_days: int = 30,
    ) -> List[NotionCalendarEvent]:
        """
        Get all pages in database that have a set date property as calendar events.
        Only events from the past "cutoff_days" nr of days are retured.
        """

        logger.info("Getting all pages from Notion.")

        database_object = self.get_database(database)
        property_ids = []
        for property in [
            database.title_property,
            database.date_property,
            database.icon_property,
        ]:
            property_ids.append(
                urllib.parse.unquote(database_object["properties"][property]["id"])
            )

        body = {
            "filter": {
                "property": database.date_property,
                "date": {"is_not_empty": True},
            },
            "sorts": [{"property": database.date_property, "direction": "descending"}],
        }
        query = {"filter_properties": property_ids}

        response = self.post_paginated(
            f"databases/{database.id}/query",
            body,
            database,
            query,
        )

        events = map(partial(page_to_calendar_event, database=database), response)

        def _date_cutoff(event: CalendarEvent):
            return event.date.start >= dt.now().subtract(days=cutoff_days)

        events = list(takewhile(_date_cutoff, events))

        return events
