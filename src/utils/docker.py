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
from docker.models.images import Image, ImageCollection
from docker.models.networks import Network
from docker.models.volumes import Volume


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


class VolumeCollectionProto(Protocol):
    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Volume]: ...
    def get(self, volume_id: str) -> Volume: ...


class NetworkCollectionProto(Protocol):
    def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Network]: ...
    def get(self, volume_id: str) -> Network: ...


class DockerClientProto(Protocol):
    @property
    def containers(self) -> ContainerCollectionProto: ...

    @property
    def images(self) -> ImageCollection: ...

    @property
    def volumes(self) -> VolumeCollectionProto: ...

    @property
    def networks(self) -> NetworkCollectionProto: ...

    def events(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        decode: bool = False,
    ) -> Iterator[Dict[str, Any]]: ...


class DockerObject(Protocol):
    @property
    def attrs(self) -> dict[str, Any]: ...


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
    return cast(DockerClientProto, from_env())


def get_attribute(obj: DockerObject, attribute: str, default: Any | None = None) -> Any:
    keys = attribute.split(".")

    attrs = obj.attrs
    current = attrs

    try:
        for key in keys:
            current = current[key]

        return current
    except (KeyError, TypeError):
        return default


def get_container_created_at(container: Container) -> str:
    return get_attribute(container, "Created")


def get_container_started_at(container: Container) -> str | None:
    return get_attribute(container, "State.StartedAt")


def get_container_image(container: Container) -> str | None:
    if container.image and len(container.image.tags) > 0:
        return container.image.tags[0]

    return None


def get_container_cmd(container: Container) -> str | None:
    cmd = get_attribute(container, "Config.Cmd")

    if cmd and isinstance(cmd, str):
        return cmd

    if cmd and isinstance(cmd, list):
        return " ".join(cast(list[str], cmd))

    return None


def get_container_entrypoint(container: Container) -> str | None:
    entrypoint = get_attribute(container, "Config.Entrypoint")

    if entrypoint and isinstance(entrypoint, str):
        return entrypoint

    if entrypoint and isinstance(entrypoint, list):
        return " ".join(cast(list[str], entrypoint))

    return None


def get_container_restart_policy(container: Container) -> str:
    policy = get_attribute(container, "HostConfig.RestartPolicy", {})

    return policy.get("Name", "no")


def get_container_environment_variables(
    container: Container,
) -> dict[str, str]:
    env = get_attribute(container, "Config.Env", [])

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
    raw = get_attribute(container, "NetworkSettings.Networks")

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
    raw = get_attribute(container, "Mounts", [])

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
    raw = get_attribute(container, "HostConfig.PortBindings", [])

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


def get_images() -> list[Image]:
    images = get_docker_client().images.list()
    images.sort(key=lambda image: image.short_id)

    return images


def get_image_last_tag(image: Image) -> str | None:
    return image.tags[0] if len(image.tags) > 0 else None


def get_image_architecture(image: Image) -> str:
    return get_attribute(image, "Architecture", "unknown")


def get_image_os(image: Image) -> str:
    return get_attribute(image, "Os", "unknown")


def get_image_size(image: Image) -> int:
    return get_attribute(image, "Size", 0)


def get_image_created_at(image: Image) -> str:
    return get_attribute(image, "Created")


def get_image(identifier: str) -> Image:
    return get_docker_client().images.get(identifier)


def get_volumes() -> list[Volume]:
    return get_docker_client().volumes.list()


def get_networks() -> list[Network]:
    return get_docker_client().networks.list()


def get_network_driver(network: Network) -> str:
    return get_attribute(network, "Driver", "unknown")
