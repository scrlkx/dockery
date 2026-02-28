import threading
from collections.abc import Callable
from typing import Any, TypedDict, cast

from gi.repository import GLib

from .docker import get_client


class DockerEvent(TypedDict, total=False):
    Type: str
    Action: str
    id: str
    status: str
    time: int
    timeNano: int
    Actor: dict[str, Any]


_Listener = tuple[Callable[[], None], str | None]

_listeners: list[_Listener] = []
_listeners_lock = threading.Lock()
_started = False  # pylint: disable=invalid-name


def _start_listener() -> None:
    global _started

    if _started:
        return

    _started = True

    def _listen() -> None:
        global _started

        client = get_client()

        try:
            for (
                _event
            ) in client.events(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType] pylint: disable=line-too-long
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
                container_id = event.get("Actor", {}).get("ID")

                with _listeners_lock:
                    for callback, filter_id in _listeners:
                        if filter_id is None or filter_id == container_id:
                            GLib.idle_add(callback)
        except Exception:
            _started = False

    thread = threading.Thread(
        target=_listen,
        name="docker_events",
        daemon=True,
    )

    thread.start()


def on_containers_change(on_change: Callable[[], None]) -> None:
    with _listeners_lock:
        _listeners.append((on_change, None))

    _start_listener()


def on_container_change(on_change: Callable[[], None], container_id: str) -> None:
    with _listeners_lock:
        _listeners.append((on_change, container_id))

    _start_listener()


def unsubscribe(on_change: Callable[[], None]) -> None:
    with _listeners_lock:
        _listeners[:] = [
            (callback, fid) for callback, fid in _listeners if callback != on_change
        ]
