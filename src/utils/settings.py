from typing import List, Tuple

from gi.repository import Gio, GLib

SCHEMA_ID = "com.scrlkx.dockery"


def get_settings() -> Gio.Settings:
    """Gets the application settings."""
    return Gio.Settings.new(SCHEMA_ID)


def get_connections() -> List[Tuple[str, str]]:
    """Gets the list of saved connections."""
    settings = get_settings()
    variant = settings.get_value("connections")
    return variant.unpack()


def add_connection(name: str, uri: str) -> None:
    """Adds a new connection to the settings."""
    settings = get_settings()
    connections = get_connections()

    # Don't add if name or URI already exist.
    if any(c_name == name or c_uri == uri for c_name, c_uri in connections):
        print(f"Warning: Connection with name '{name}' or URI '{uri}' already exists.")
        return

    connections.append((name, uri))

    variant = GLib.Variant("a(ss)", connections)
    settings.set_value("connections", variant)


def remove_connection(name: str, uri: str) -> None:
    """Removes a connection from the settings."""
    settings = get_settings()
    connections = get_connections()

    new_connections = [
        (c_name, c_uri)
        for c_name, c_uri in connections
        if c_name != name or c_uri != uri
    ]

    variant = GLib.Variant("a(ss)", new_connections)
    settings.set_value("connections", variant)
