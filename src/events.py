import threading
from collections.abc import Callable
from typing import Any, TypedDict, cast

from docker.models.containers import Container
from gi.repository import GLib

from .client import get_docker_client


class DockerEvent(TypedDict, total=False):
    Type: str
    Action: str
    id: str
    status: str
    time: int
    timeNano: int
    Actor: dict[str, Any]


def on_containers_change(on_change: Callable[[], None]):
    client = get_docker_client()

    def _listen() -> None:
        for (
            _
        ) in client.events(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            decode=True,
            filters={
                "type": "container",
                "event": [
                    "start",
                    "stop",
                    "die",
                    "pause",
                    "unpause",
                    "restart",
                    "destroy",
                ],
            },
        ):
            GLib.idle_add(on_change)

    thread = threading.Thread(
        target=_listen,
        name="docker_on_containers_chage",
        daemon=True,
    )

    thread.start()


def on_container_change(on_change: Callable[[], None], container: Container):
    client = get_docker_client()

    def _listen():
        for (
            _event
        ) in client.events(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            decode=True,
            filters={
                "type": "container",
                "event": [
                    "start",
                    "stop",
                    "die",
                    "pause",
                    "unpause",
                    "restart",
                    "destroy",
                ],
            },
        ):
            event = cast(DockerEvent, _event)

            if container.id == event.get("Actor", {}).get("ID"):
                GLib.idle_add(on_change)

    thread = threading.Thread(
        target=_listen,
        name="docker_on_container_chage",
        daemon=True,
    )

    thread.start()
