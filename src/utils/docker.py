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

    def info(self) -> Dict[str, Any]: ...


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
    return get_attribute(container, "Config.Image")


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

    return policy.get("Name")


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
    containers = get_docker_client().containers.list(all=True)
    containers.sort(key=lambda item: item.name)

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
    container.remove()


def get_container_actions(container: Container) -> list[str]:
    actions = {
        "running": ["stop", "pause", "restart", "kill", "console"],
        "restarting": ["stop", "kill"],
        "paused": ["resume", "kill"],
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
    return get_attribute(image, "Architecture")


def get_image_os(image: Image) -> str:
    return get_attribute(image, "Os")


def get_image_size(image: Image) -> int:
    return get_attribute(image, "Size", 0)


def get_image_created_at(image: Image) -> str:
    return get_attribute(image, "Created")


def get_image(identifier: str) -> Image:
    return get_docker_client().images.get(identifier)


def get_volumes() -> list[Volume]:
    volumes = get_docker_client().volumes.list()
    volumes.sort(key=lambda volume: volume.name)

    return volumes


def get_volume(identifier: str) -> Volume:
    return get_docker_client().volumes.get(identifier)


def get_volume_short_name(volume: Volume) -> str:
    if len(volume.name) > 50:
        return volume.name[:20]

    return volume.name


def get_volume_driver(volume: Volume) -> str:
    return get_attribute(volume, "Driver")


def get_volume_mount_path(volume: Volume) -> str:
    return get_attribute(volume, "Mountpoint")


def get_volume_created_at(volume: Volume) -> str:
    return get_attribute(volume, "CreatedAt")


def get_networks() -> list[Network]:
    networks = get_docker_client().networks.list()
    networks.sort(key=lambda network: network.name or network.short_id)

    return networks


def get_network_driver(network: Network) -> str:
    return get_attribute(network, "Driver")


def get_network_created_at(network: Network) -> str:
    return get_attribute(network, "Created")


def get_network(identifier: str) -> Network:
    return get_docker_client().networks.get(identifier)


def get_system_info() -> dict[str, Any]:
    return get_docker_client().info()
