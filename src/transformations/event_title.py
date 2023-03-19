from models.event import CalendarEvent


def format_event_title(event: CalendarEvent) -> str:
    """
    Format plain Notion page title to indicate database or page properties.
    """

    # Determine icon based on the given page property
    icon = event.database.icon_value_mapping.get(
        event.icon_property_value,
        event.database.icon_default,
    )

    return f"{icon} {event.title}"
