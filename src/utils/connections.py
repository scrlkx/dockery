from gi.repository import Gio


def get_connections() -> list[str]:
    settings = Gio.Settings.new("com.scrlkx.dockery")
    return list(settings.get_strv("connections"))


def add_connection(uri: str) -> None:
    settings = Gio.Settings.new("com.scrlkx.dockery")
    connections = list(settings.get_strv("connections"))

    if uri not in connections:
        connections.append(uri)
        settings.set_strv("connections", connections)
