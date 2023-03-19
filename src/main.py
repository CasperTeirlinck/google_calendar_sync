import logging
import datetime as dt
from pathlib import Path
import sys
import requests
import yaml
import argparse
from typing import Optional

from api_client.google import GCalendar
from api_client.notion import Notion
from models.config import Config
from models.database import Database
from common.utils import are_events_equivalent, map_events

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(push_url: Optional[str] = None):
    """
    Sync dated notion pages in all configured databases to the specified Google Calendars.
    """

    # Config
    with open(Path(__file__).parents[1] / "config" / "config.yaml", "r") as f:
        config = Config.from_dict(yaml.safe_load(f))

    # API clients
    gcalendar = GCalendar()
    notion = Notion()

    # Sync all databases
    for database in config.databases:
        sync_database(notion, gcalendar, database)

    # Ping monitoring url
    if push_url:
        try:
            requests.get(push_url)
        except Exception as e:
            logger.warning(f"Failed to reach Uptime Kuma push url: {e}.")

    logger.info("Done!")


def sync_database(notion: Notion, gcalendar: GCalendar, database: Database) -> None:
    """
    Sync dated notion pages for a single database to the specified Google Calendar.
    """

    logger.info(f"Starting to sync database {database.name}.")

    # Get events from Notion and Google Calendar
    logger.info("Getting all pages from Notion...")
    events_notion = notion.get_events(database)
    logger.info("Getting all events from Google Calendar...")
    events_google = gcalendar.get_events(database)

    # Map events from Notion to events from Google Calendar
    events = map_events(events_notion, events_google)

    # Create/Update/Delete events
    for event_notion, event_google in events:
        # Update event
        if event_notion and event_google:
            # Check if update is needed
            if are_events_equivalent(event_notion, event_google):
                continue

            event_notion.google_event_id = event_google.google_event_id
            gcalendar.update_event(event_notion)

        # Add event
        if event_notion and not event_google:
            # Dont create new events that are older that 5 days
            if event_notion.date < dt.datetime.now() - dt.timedelta(days=5):
                continue

            gcalendar.create_event(event_notion)

        # Remove event
        if not event_notion and event_google:
            gcalendar.delete_event(event_google)

    logger.info(f"Done syncing database {database.name}!")


if __name__ == "__main__":
    # Optional Uptime Kuma push url for monitoring
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--url", required=False)
    args = arg_parser.parse_args()

    main(push_url=args.url)

    sys.stdout.flush()
