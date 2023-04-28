from typing import Type, Union
import datetime
import pendulum as dt

from src.models.event import CalendarEvent


def is_older_than(event: Type[CalendarEvent], cutoff_days: int = 5) -> bool:
    """
    See if the given event is older that the cutoff
    """

    return event.date.start < dt.now().subtract(days=cutoff_days)


def to_datetime(date: Union[datetime.datetime, datetime.date]) -> dt.DateTime:
    """
    Convert a datetime/date object to a pendulum datetime object.
    """

    if type(date) is datetime.date:
        date = datetime.datetime.combine(date, datetime.time.min)

    return dt.instance(date)
