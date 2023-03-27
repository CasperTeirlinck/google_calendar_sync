from typing import Type
import pytz
import datetime as dt

from models.event import CalendarEvent


def get_timezone_name(date: dt.datetime) -> str:
    """
    Return IANA timezone name from the datetime object.
    """

    matching_timezones = [
        tz
        for tz in pytz.common_timezones
        if dt.datetime.now(pytz.timezone(tz)).utcoffset() == date.utcoffset()
    ]
    return matching_timezones[0]


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
