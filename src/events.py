import threading

from gi.repository import GLib

from .client import get_docker_client


def on_containers_chage(on_change):
    client = get_docker_client()

    def _listen():
        for _ in client.events(
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
        name="docker-events",
        daemon=True,
    )

    thread.start()


def on_container_chage(on_change, container):
    client = get_docker_client()

    def _listen():
        for event in client.events(
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
            if container == event.get("Actor").get("ID"):
                GLib.idle_add(on_change)

    thread = threading.Thread(
        target=_listen,
        name="docker-events",
        daemon=True,
    )

    thread.start()
