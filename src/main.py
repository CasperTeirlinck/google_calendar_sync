import logging
from pathlib import Path
import sys
import requests
import yaml
import argparse
from typing import Optional

from api_client.google import GCalendar
from api_client.ical import ICal
from api_client.notion import Notion
from jobs.sync_ical import sync_icalendar
from jobs.sync_notion import sync_database
from models.config import Config

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(push_url: Optional[str] = None):
    # Config
    with open(Path(__file__).parents[1] / "config" / "config.yaml", "r") as f:
        config = Config.from_dict(yaml.safe_load(f))

    # API clients
    gcalendar = GCalendar()
    notion = Notion()
    ical = ICal()

    # Sync all icalendars
    for icalendar in config.icals:
        sync_icalendar(ical, gcalendar, icalendar)

    return

    # Sync all notion databases
    for database in config.databases:
        sync_database(notion, gcalendar, database)

    # Ping monitoring url
    if push_url:
        try:
            requests.get(push_url)
        except Exception as e:
            logger.warning(f"Failed to reach Uptime Kuma push url: {e}.")

    logger.info("Done!")


if __name__ == "__main__":
    # Optional Uptime Kuma push url for monitoring
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--url", required=False)
    args = arg_parser.parse_args()

    main(push_url=args.url)

    sys.stdout.flush()
