from datetime import datetime
from typing import Any, Optional

from docker.models.containers import Container


def get_container_attribute(
    container: Container, attribute: str, default: Optional[Any] = None
) -> Optional[Any]:
    attrs = container.attrs
    keys = attribute.split(".")

    current = attrs
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def get_container_started_at(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    original = get_container_attribute(container, "State.StartedAt")

    return iso_to_local(original) if original else default


def get_container_image(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    return (
        container.image.tags[0]
        if container.image and len(container.image.tags) > 0
        else default
    )


def get_container_status_label(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    labels = {
        "running": "Running",
        "paused": "Paused",
        "restarting": "Restarting",
        "created": "Created",
        "exited": "Exited",
        "dead": "Dead",
    }

    return labels[container.status] or default


def iso_to_local(original: str) -> str:
    date_time = datetime.fromisoformat(original.replace("Z", "+00:00"))
    local_date_time = date_time.astimezone()

    return local_date_time.strftime("%c")
