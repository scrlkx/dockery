from functools import lru_cache
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    TypedDict,
    cast,
)

from docker import from_env
from docker.models.containers import Container


class ContainerCollectionProto(Protocol):
    def list(
        self,
        # pylint: disable=redefined-builtin
        all: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        sparse: bool = False,
        ignore_removed: bool = False,
    ) -> List[Container]: ...
    def get(self, container_id: str) -> Container: ...


class DockerClientProto(Protocol):
    @property
    def containers(self) -> ContainerCollectionProto: ...

    def events(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        decode: bool = False,
    ) -> Iterator[Dict[str, Any]]: ...


class DockerNetworkInfo(TypedDict, total=False):
    IPAddress: str
    Gateway: str
    NetworkID: str
    EndpointID: str


DockerMount = dict[str, str]


class DockerPortBinding(TypedDict, total=False):
    HostIp: str
    HostPort: str


@lru_cache(maxsize=1)
def get_docker_client() -> DockerClientProto:
    return from_env()


def get_container_attribute(
    container: Container, attribute: str, default: Any | None = None
) -> Any:
    keys = attribute.split(".")

    attrs = container.attrs
    current = attrs

    try:
        for key in keys:
            current = current[key]

        return current
    except (KeyError, TypeError):
        return default


def get_container_created_at(container: Container) -> str:
    return get_container_attribute(container, "Created")


def get_container_started_at(container: Container) -> str | None:
    return get_container_attribute(container, "State.StartedAt")


def get_container_image(container: Container) -> str | None:
    if container.image and len(container.image.tags) > 0:
        return container.image.tags[0]

    return None


def get_container_cmd(container: Container) -> str | None:
    cmd = get_container_attribute(container, "Config.Cmd")

    if cmd and isinstance(cmd, str):
        return cmd

    if cmd and isinstance(cmd, list):
        return " ".join(cast(list[str], cmd))

    return None


def get_container_entrypoint(container: Container) -> str | None:
    entrypoint = get_container_attribute(container, "Config.Entrypoint")

    if entrypoint and isinstance(entrypoint, str):
        return entrypoint

    if entrypoint and isinstance(entrypoint, list):
        return " ".join(cast(list[str], entrypoint))

    return None


def get_container_restart_policy(container: Container) -> str:
    policy = get_container_attribute(container, "HostConfig.RestartPolicy", {})

    return policy.get("Name", "no")


def get_container_environment_variables(
    container: Container,
) -> dict[str, str]:
    env = get_container_attribute(container, "Config.Env", [])

    if not isinstance(env, Iterable):
        return {}

    variables: dict[str, str] = {}

    for item in cast(list[str], env):
        # split only on first "="
        key, sep, value = item.partition("=")

        if not sep:
            continue

        variables[key] = value

    return variables


def get_container_networks(
    container: Container,
) -> dict[str, str]:
    raw = get_container_attribute(container, "NetworkSettings.Networks")

    if not isinstance(raw, dict):
        return {}

    net = cast(dict[str, DockerNetworkInfo], raw)
    networks: dict[str, str] = {}

    for key, item in net.items():
        ip = item.get("IPAddress")

        if ip:
            networks[key] = ip

    return networks


def get_container_volumes(
    container: Container,
) -> dict[str, str]:
    raw = get_container_attribute(container, "Mounts", [])

    if not isinstance(raw, Iterable):
        return {}

    mounts = cast(Iterable[DockerMount], raw)
    volumes: dict[str, str] = {}

    for item in mounts:
        name = item.get("Name") or item.get("Source")
        mode = item.get("Mode")

        if name and mode:
            volumes[name] = mode

    return volumes


def get_container_ports(
    container: Container,
) -> dict[str, str]:
    raw = get_container_attribute(container, "HostConfig.PortBindings", [])

    if not isinstance(raw, dict):
        return {}

    bindings = cast(dict[str, list[DockerPortBinding]], raw)
    ports: dict[str, str] = {}

    for key, items in bindings.items():
        ports[key] = ", ".join(binding.get("HostPort", "-") for binding in items)

    return ports


def get_container(name: str) -> Container:
    return get_docker_client().containers.get(name)


def get_containers() -> list[Container]:
    status_order = {
        "running": 0,
        "paused": 1,
        "restarting": 2,
        "created": 3,
        "exited": 4,
        "dead": 5,
    }

    containers = get_docker_client().containers.list(all=True)
    containers.sort(key=lambda item: status_order.get(item.status, 99))

    return containers


def start_container(name: str) -> None:
    get_container(name).start()


def stop_container(name: str) -> None:
    get_container(name).stop()


def pause_container(name: str) -> None:
    get_container(name).pause()


def unpause_container(name: str) -> None:
    get_container(name).unpause()


def restart_container(name: str) -> None:
    get_container(name).restart()


def kill_container(name: str) -> None:
    get_container(name).kill()


def remove_container(name: str) -> None:
    container = get_docker_client().containers.get(name)
    container.kill()


def get_container_actions(container: Container) -> list[str]:
    actions = {
        "running": ["stop", "pause", "restart", "kill"],
        "restarting": ["stop", "kill"],
        "paused": ["resume", "stop", "kill"],
        "stopped": ["start", "remove"],
        "exited": ["start", "remove"],
        "created": ["start", "remove"],
    }

    return actions.get(container.status, ["start", "stop"])


def get_container_next_action(container: Container) -> str:
    actions = get_container_actions(container)

    return actions[0]
