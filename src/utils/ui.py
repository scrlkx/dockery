from datetime import datetime
from typing import Callable

from docker.models.containers import Container
from gi.repository import Adw

from ..components.connection_error_dialog import ConnectionErrorDialog
from ..components.error_dialog import ErrorDialog
from .docker import disconnect
from .i18n import _

_window: Adw.ApplicationWindow | None = None  # pylint: disable=invalid-name
_connection_error_dialog_open = False  # pylint: disable=invalid-name


def set_main_window(window: Adw.ApplicationWindow) -> None:
    global _window
    _window = window


def show_error_dialog(message: str) -> None:
    if not _window:
        print(f"Error dialog not shown because main window is not set: {message}")
        return

    dialog = ErrorDialog(
        message=message,
        transient_for=_window,
    )
    dialog.present()


def show_connection_error_dialog(
    message: str, on_reconnect: Callable[[], None]
) -> None:
    global _connection_error_dialog_open

    if _connection_error_dialog_open:
        return

    assert _window is not None

    _connection_error_dialog_open = True

    dialog = ConnectionErrorDialog(message=message)

    def on_response(message_dialog: Adw.MessageDialog, response: str) -> None:
        global _connection_error_dialog_open

        _connection_error_dialog_open = False
        message_dialog.close()

        if response == "disconnect":
            disconnect()

            if _window is not None:
                show_connections = getattr(_window, "show_connections_view", None)

                if callable(show_connections):
                    show_connections()

            return

        on_reconnect()

    dialog.connect("response", on_response)
    dialog.present()


def get_container_status_label(container: Container) -> str:
    labels = {
        "running": _("Running"),
        "paused": _("Paused"),
        "restarting": _("Restarting"),
        "created": _("Created"),
        "exited": _("Exited"),
        "dead": _("Dead"),
    }

    return labels.get(container.status, _("Dead"))


def get_container_status_class(container: Container) -> str | None:
    classes = {
        "running": "tag-green",
        "paused": "tag-blue",
        "restarting": "tag-red",
        "created": "tag-gray",
        "exited": "tag-orange",
        "dead": "tag-black",
    }

    return classes.get(container.status)


def get_container_action_label(action: str) -> str | None:
    actions = {
        "start": _("Start"),
        "stop": _("Stop"),
        "pause": _("Pause"),
        "resume": _("Resume"),
        "restart": _("Restart"),
        "kill": _("Kill"),
        "remove": _("Remove"),
        "logs": _("Logs"),
        "console": _("Console"),
    }

    return actions.get(action)


def get_container_action_icon(action: str) -> str | None:
    actions = {
        "start": "media-playback-start-symbolic",
        "stop": "media-playback-stop-symbolic",
        "pause": "media-playback-pause-symbolic",
        "resume": "media-playback-start-symbolic",
        "restart": "system-reboot-symbolic",
        "kill": "process-stop-symbolic",
        "remove": "user-trash-symbolic",
        "logs": "logs-symbolic",
        "console": "utilities-terminal-symbolic",
    }

    return actions.get(action)


def iso_to_local(original: str | int | None) -> str:
    if original is None:
        return "-"

    if isinstance(original, int):
        date_time = datetime.fromtimestamp(original)
    else:
        date_time = datetime.fromisoformat(original)

    local_date_time = date_time.astimezone()

    return local_date_time.strftime("%x %H:%M")


def humanize_mount_mode(mode: str | None) -> str:
    if not mode:
        return _("Read-write")

    flags = set(mode.split(","))

    if "ro" in flags:
        access = _("Read-only")
    else:
        access = _("Read-write")

    extras: list[str] = []

    if "z" in flags:
        extras.append(f"{_('shared')} (SELinux)")
    elif "Z" in flags:
        extras.append(f"{_('private')} (SELinux)")

    if "rshared" in flags:
        extras.append(_("shared"))
    elif "rslave" in flags:
        extras.append(_("slave"))
    elif "rprivate" in flags:
        extras.append(_("private"))

    if extras:
        return f"{access} ({', '.join(extras)})"

    return access


def humanize_size(size: int | None) -> str:
    if size is None:
        return "-"

    value = float(size)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"
