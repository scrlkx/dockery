import threading
from collections.abc import Callable
from typing import Literal, TypeAlias, TypedDict, cast

from gi.repository import GLib

from .docker import get_client


class DockerEventActor(TypedDict, total=False):
    ID: str


class DockerEvent(TypedDict, total=False):
    Type: str
    Action: str
    id: str
    status: str
    time: int
    timeNano: int
    Actor: DockerEventActor


_Listener: TypeAlias = tuple[
    Callable[[], None],
    Literal["container", "image", "volume"],
    str | None,
]

_listeners: list[_Listener] = []
_listeners_lock = threading.Lock()
_started = False  # pylint: disable=invalid-name


def _start_listener() -> None:
    global _started

    if _started:
        return

    _started = True

    def notify_listener(callback: Callable[[], None]) -> bool:
        callback()

        return False

    def _listen() -> None:
        global _started

        client = get_client()

        try:
            for (
                _event
            ) in client.events(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType] pylint: disable=line-too-long
                decode=True,
            ):
                event = cast(DockerEvent, _event)
                event_type = event.get("Type")
                event_id = event.get("Actor", {}).get("ID") or event.get("id")

                if event_type not in {"container", "image", "volume"}:
                    continue

                with _listeners_lock:
                    listeners = list(_listeners)

                for callback, listener_type, filter_id in listeners:
                    if listener_type != event_type:
                        continue

                    if filter_id is None or filter_id == event_id:
                        GLib.idle_add(notify_listener, callback)
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
        _listeners.append((on_change, "container", None))

    _start_listener()


def on_container_change(on_change: Callable[[], None], container_id: str) -> None:
    with _listeners_lock:
        _listeners.append((on_change, "container", container_id))

    _start_listener()


def on_images_change(on_change: Callable[[], None]) -> None:
    with _listeners_lock:
        _listeners.append((on_change, "image", None))

    _start_listener()


def on_volumes_change(on_change: Callable[[], None]) -> None:
    with _listeners_lock:
        _listeners.append((on_change, "volume", None))

    _start_listener()


def unsubscribe(on_change: Callable[[], None]) -> None:
    with _listeners_lock:
        _listeners[:] = [
            (callback, resource_type, fid)
            for callback, resource_type, fid in _listeners
            if callback != on_change
        ]
