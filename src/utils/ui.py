from datetime import datetime

from docker.models.containers import Container


def get_container_status_label(container: Container) -> str | None:
    labels = {
        "running": "Running",
        "paused": "Paused",
        "restarting": "Restarting",
        "created": "Created",
        "exited": "Exited",
        "dead": "Dead",
    }

    return labels.get(container.status)


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
        "start": "Start",
        "stop": "Stop",
        "pause": "Pause",
        "resume": "Resume",
        "restart": "Restart",
        "kill": "Kill",
        "remove": "Remove",
    }

    return actions.get(action)


def get_container_action_icon(action: str) -> str | None:
    actions = {
        "start": "play.svg",
        "stop": "circle-crossed.svg",
        "pause": "pause.svg",
        "resume": "arrow-pointing-away.svg",
        "restart": "reload.svg",
        "kill": "cross.svg",
        "remove": "trash.svg",
    }

    return actions.get(action)


def iso_to_local(original: str) -> str:
    date_time = datetime.fromisoformat(original.replace("Z", "+00:00"))
    local_date_time = date_time.astimezone()

    return local_date_time.strftime("%c")


def humanize_mount_mode(mode: str | None) -> str:
    if not mode:
        return "Read-write"

    flags = set(mode.split(","))

    if "ro" in flags:
        access = "Read-only"
    else:
        access = "Read-write"

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
