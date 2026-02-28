from typing import TypedDict


class ConnectionProfile(TypedDict, total=False):
    name: str
    kind: str
    uri: str
    host: str
    port: int
    user: str
    identity_file: str
    jump_host: str
    jump_port: int
    jump_user: str
    jump_identity_file: str


def get_profile_display_name(profile: ConnectionProfile) -> str:
    kind = profile.get("kind", "unix")

    if kind == "ssh":
        host = profile.get("host", "")
        user = profile.get("user")
        port = profile.get("port", 22)

        name = f"{user}@{host}" if user else host

        if port and port != 22:
            name += f":{port}"

        return name

    return profile.get("uri", "")


def build_ssh_uri(profile: ConnectionProfile) -> str:
    host = profile.get("host", "localhost")
    port = profile.get("port", 22)
    user = profile.get("user")

    if user:
        return f"ssh://{user}@{host}:{port}"

    return f"ssh://{host}:{port}"
