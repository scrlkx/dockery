import threading
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    TypedDict,
    TypeVar,
    cast,
)

from docker import DockerClient
from docker.constants import (
    MINIMUM_DOCKER_API_VERSION,
)
from docker.errors import DockerException
from docker.models.containers import Container
from docker.models.images import Image, ImageCollection
from docker.models.networks import Network
from docker.models.volumes import Volume
from paramiko.ssh_exception import ChannelException, SSHException
from requests import exceptions as requests_exceptions

from .connection_profile import ConnectionProfile, build_ssh_uri
from .docker_ssh import DockerySSHAdapter


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

    @property
    def api(self) -> Any: ...

    def events(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        decode: bool = False,
    ) -> Iterator[Dict[str, Any]]: ...

    def info(self) -> Dict[str, Any]: ...

    def ping(self) -> None: ...

    def close(self) -> None: ...


class DockerImagesAPIProto(Protocol):
    def images(
        self,
        name: str | None = None,
        quiet: bool = False,
        all: bool = False,  # pylint: disable=redefined-builtin
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...


class DockerImagesClientProto(Protocol):
    api: DockerImagesAPIProto


class DockerLowLevelAPIProto(Protocol):
    def containers(
        self,
        all: bool = False,  # pylint: disable=redefined-builtin
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...

    def volumes(self) -> dict[str, Any]: ...

    def networks(
        self,
        names: list[str] | None = None,
        ids: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...


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


DOCKER_CALL_TIMEOUT_SECONDS = 10
DOCKER_CONNECTION_RETRY_ATTEMPTS = 2
SSH_NUM_POOLS = 1
SSH_MAX_POOL_SIZE = 4
_CONNECTION_FAILURE_MARKERS = (
    "connection aborted",
    "connection refused",
    "connection reset",
    "connection broken",
    "broken pipe",
    "timed out",
    "timeout",
    "unreachable",
    "cannot connect",
)

_client: DockerClientProto | None = None  # pylint: disable=invalid-name
_profile: ConnectionProfile | None = None  # pylint: disable=invalid-name
_client_lock = threading.Lock()
T = TypeVar("T")


def _build_ssh_client(profile: ConnectionProfile) -> DockerClient:
    uri = build_ssh_uri(profile)
    client = DockerClient(
        base_url=uri,
        timeout=DOCKER_CALL_TIMEOUT_SECONDS,
        version=MINIMUM_DOCKER_API_VERSION,
        use_ssh_client=True,
        max_pool_size=SSH_MAX_POOL_SIZE,
    )

    # docker SDK exposes these knobs as private attrs;
    # access dynamically to avoid protected-member/type checker diagnostics.
    api = cast(Any, client.api)
    custom_adapter = getattr(api, "_custom_adapter", None)

    if custom_adapter is not None:
        custom_adapter.close()

    adapter = DockerySSHAdapter(
        profile,
        timeout=DOCKER_CALL_TIMEOUT_SECONDS,
        pool_connections=SSH_NUM_POOLS,
        max_pool_size=SSH_MAX_POOL_SIZE,
    )

    setattr(api, "_custom_adapter", adapter)

    api.mount("http+docker://ssh", adapter)

    retrieve_server_version = cast(Any, getattr(api, "_retrieve_server_version", None))

    if callable(retrieve_server_version):
        setattr(api, "_version", retrieve_server_version())

    return client


def _build_local_client(profile: ConnectionProfile) -> DockerClient:
    uri = profile.get("uri", "unix:///var/run/docker.sock")
    return DockerClient(base_url=uri, timeout=DOCKER_CALL_TIMEOUT_SECONDS)


def _build_client_for_profile(profile: ConnectionProfile) -> DockerClientProto:
    kind = profile.get("kind", "unix")

    if kind == "tcp":
        raise RuntimeError("TCP connections are no longer supported")

    client = (
        _build_ssh_client(profile) if kind == "ssh" else _build_local_client(profile)
    )

    return cast(DockerClientProto, client)


def connect(profile: ConnectionProfile) -> None:
    global _client, _profile

    client = _build_client_for_profile(profile)
    client.ping()

    with _client_lock:
        _client = client
        _profile = cast(ConnectionProfile, dict(profile))


def disconnect() -> None:
    global _client, _profile

    with _client_lock:
        if _client is not None:
            _client.close()

        _client = None
        _profile = None


def get_client() -> DockerClientProto:
    if _client is None:
        raise RuntimeError("Not connected to Docker")

    return _client


def get_api() -> DockerLowLevelAPIProto:
    return cast(DockerLowLevelAPIProto, get_client().api)


def _is_connection_failure(exception: Exception) -> bool:
    if isinstance(exception, (ChannelException, SSHException)):
        return True

    if isinstance(
        exception,
        (
            requests_exceptions.ConnectionError,
            requests_exceptions.Timeout,
        ),
    ):
        return True

    if isinstance(exception, DockerException):
        message = str(exception).lower()
        return any(marker in message for marker in _CONNECTION_FAILURE_MARKERS)

    return False


def _reconnect() -> None:
    global _client

    profile = _profile
    if profile is None:
        raise RuntimeError("Not connected to Docker")

    new_client = _build_client_for_profile(profile)
    new_client.ping()

    with _client_lock:
        old_client = _client
        _client = new_client

    if old_client is not None:
        old_client.close()


def _with_connection_retry(operation: Callable[[], T]) -> T:
    for attempt in range(DOCKER_CONNECTION_RETRY_ATTEMPTS):
        try:
            return operation()
        except Exception as exception:
            is_last_attempt = attempt >= (DOCKER_CONNECTION_RETRY_ATTEMPTS - 1)

            if is_last_attempt or not _is_connection_failure(exception):
                raise

            _reconnect()

    raise RuntimeError("Unexpected retry state")


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
    return _with_connection_retry(lambda: get_client().containers.get(name))


def get_containers() -> list[Container]:
    def operation() -> list[Container]:
        api = get_api()
        response = api.containers(all=True)

        containers: list[Container] = []

        for item in response:
            names = cast(list[str], item.get("Names", []))

            if names:
                item["Name"] = names[0].lstrip("/")

            containers.append(cast(Any, Container)(attrs=item, client=api))

        containers.sort(key=lambda item: item.name or "")

        return containers

    return _with_connection_retry(operation)


def start_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).start())


def stop_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).stop())


def pause_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).pause())


def unpause_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).unpause())


def restart_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).restart())


def kill_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).kill())


def remove_container(name: str) -> None:
    _with_connection_retry(lambda: get_client().containers.get(name).remove())


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
    def operation() -> list[Image]:
        client = get_client()
        response = cast(DockerImagesClientProto, client.images.client).api.images()

        images = [Image(attrs=r, client=client.images.client) for r in response]
        images.sort(key=lambda image: image.short_id)

        return images

    return _with_connection_retry(operation)


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
    return _with_connection_retry(lambda: get_client().images.get(identifier))


def get_volumes() -> list[Volume]:
    def operation() -> list[Volume]:
        api = get_api()
        response = api.volumes()

        raw_volumes = cast(list[dict[str, Any]], response.get("Volumes", []))

        volumes = [
            cast(Any, Volume)(attrs=row_volume, client=api)
            for row_volume in raw_volumes
        ]

        volumes.sort(key=lambda volume: volume.name)

        return volumes

    return _with_connection_retry(operation)


def get_volume(identifier: str) -> Volume:
    return _with_connection_retry(lambda: get_client().volumes.get(identifier))


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
    def operation() -> list[Network]:
        api = get_api()
        response = api.networks()

        networks = [cast(Any, Network)(attrs=item, client=api) for item in response]
        networks.sort(key=lambda network: network.name or network.short_id)

        return networks

    return _with_connection_retry(operation)


def get_network_driver(network: Network) -> str:
    return get_attribute(network, "Driver")


def get_network_created_at(network: Network) -> str:
    return get_attribute(network, "Created")


def get_network(identifier: str) -> Network:
    return _with_connection_retry(lambda: get_client().networks.get(identifier))


def get_system_info() -> dict[str, Any]:
    return _with_connection_retry(lambda: get_client().info())
