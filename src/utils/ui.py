from datetime import datetime

from docker.models.containers import Container

from .i18n import _


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
    }

    return actions.get(action)


def iso_to_local(original: str) -> str:
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
        extras.append("shared (SELinux)")
    elif "Z" in flags:
        extras.append("private (SELinux)")

    if "rshared" in flags:
        extras.append("shared")
    elif "rslave" in flags:
        extras.append("slave")
    elif "rprivate" in flags:
        extras.append("private")

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
