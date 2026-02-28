import json
from typing import cast

from gi.repository import Gio

from .connection_profile import ConnectionProfile, get_profile_display_name


def _get_settings() -> Gio.Settings:
    return Gio.Settings.new("com.scrlkx.dockery")


def get_connections() -> list[ConnectionProfile]:
    settings = _get_settings()
    raw = settings.get_string("connection-profiles")

    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    return cast(list[ConnectionProfile], data)


def add_connection(profile: ConnectionProfile) -> None:
    settings = _get_settings()
    profiles = get_connections()

    display_name = get_profile_display_name(profile)

    for existing in profiles:
        if get_profile_display_name(existing) == display_name:
            return

    profiles.append(profile)
    settings.set_string("connection-profiles", json.dumps(profiles))


def update_connection(index: int, profile: ConnectionProfile) -> None:
    settings = _get_settings()
    profiles = get_connections()

    if 0 <= index < len(profiles):
        profiles[index] = profile
        settings.set_string("connection-profiles", json.dumps(profiles))


def remove_connection(index: int) -> None:
    settings = _get_settings()
    profiles = get_connections()

    if 0 <= index < len(profiles):
        del profiles[index]
        settings.set_string("connection-profiles", json.dumps(profiles))
