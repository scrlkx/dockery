from __future__ import annotations

import json
import os
import re
import sys
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
from docker.models.images import Image
from docker.models.networks import Network
from docker.models.volumes import Volume
from docker.utils import parse_repository_tag
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
    def run(
        self,
        image: str,
        command: Any = None,
        auto_remove: bool = False,
        remove: bool = False,
        stdout: bool = True,
        stderr: bool = False,
        detach: bool = False,
        volumes: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any: ...


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
    def images(self) -> DockerImagesCollectionProto: ...

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


class DockerImagesCollectionProto(Protocol):
    client: DockerImagesClientProto

    def get(self, name: str) -> Image: ...

    def pull(
        self,
        repository: str,
        tag: str | None = None,
        all_tags: bool = False,
        **kwargs: Any,
    ) -> Image: ...

    def remove(
        self,
        image: str,
        force: bool = False,
        noprune: bool = False,
    ) -> Any: ...


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

    def push(
        self,
        repository: str,
        tag: str | None = None,
        stream: bool = False,
        decode: bool = False,
    ) -> Any: ...

    def get_image(
        self,
        image: str,
        chunk_size: int | None = None,
    ) -> Iterable[bytes]: ...


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
VOLUME_INSPECT_IMAGE = "busybox:latest"
VOLUME_INSPECT_KEEPALIVE_COMMAND = [
    "sh",
    "-lc",
    "trap : TERM INT; while :; do sleep 3600; done",
]
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


def remove_container(name: str, force: bool = False) -> None:
    _with_connection_retry(
        lambda: get_client().containers.get(name).remove(force=force)
    )


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


def get_container_console_command(
    container_id: str, workdir: str | None = None
) -> list[str]:
    profile = _profile
    is_socket = profile is None or profile.get("kind", "unix") == "unix"
    is_ssh = profile is not None and profile.get("kind") == "ssh"

    if is_socket:
        docker_cmd = ["docker", "exec", "-it"]

        if workdir:
            docker_cmd.extend(["-w", workdir])

        docker_cmd.extend([container_id, "/bin/sh"])

        return ["flatpak-spawn", "--host", *docker_cmd]

    if is_ssh:
        assert profile is not None

        remote_console_path = os.path.join(
            os.path.dirname(__file__),
            "remote_console.py",
        )

        return [
            sys.executable,
            remote_console_path,
            json.dumps(profile),
            container_id,
        ]

    raise RuntimeError("Unsupported connection type")


def get_container_next_action(container: Container) -> str:
    actions = get_container_actions(container)

    return actions[0]


def is_socket_connection() -> bool:
    profile = _profile

    return profile is None or profile.get("kind", "unix") == "unix"


def get_images() -> list[Image]:
    def operation() -> list[Image]:
        client = get_client()
        images_client = client.images.client
        response = images_client.api.images()

        images = [Image(attrs=r, client=cast(Any, images_client)) for r in response]
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


def get_image_export_filename(image: Image) -> str:
    tag = get_image_last_tag(image)
    base_name = tag if tag else image.short_id

    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", base_name).strip("-")

    if not sanitized:
        sanitized = "image"

    return f"{sanitized}.tar"


def pull_image(reference: str) -> Image:
    repository, tag = parse_repository_tag(reference)

    return _with_connection_retry(lambda: get_client().images.pull(repository, tag=tag))


def push_image(reference: str) -> None:
    repository, tag = parse_repository_tag(reference)

    def operation() -> None:
        events = cast(
            Iterable[dict[str, Any]],
            get_api().push(repository, tag=tag, stream=True, decode=True),
        )

        for event in events:
            error = event.get("error")

            if error:
                raise RuntimeError(str(error))

    _with_connection_retry(operation)


def save_image(image_id: str, output_path: str) -> None:
    def operation() -> None:
        stream = get_api().get_image(image_id)

        with open(output_path, "wb") as handle:
            for chunk in stream:
                if chunk:
                    handle.write(chunk)

    _with_connection_retry(operation)


def remove_image(image_id: str) -> None:
    _with_connection_retry(lambda: get_client().images.remove(image=image_id))


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


def remove_volume(name: str) -> None:
    _with_connection_retry(lambda: get_client().volumes.get(name).remove())


def create_volume_inspect_container(name: str) -> str:
    def operation() -> str:
        container = get_client().containers.run(
            VOLUME_INSPECT_IMAGE,
            command=VOLUME_INSPECT_KEEPALIVE_COMMAND,
            detach=True,
            volumes={
                name: {
                    "bind": "/volume",
                    "mode": "ro",
                }
            },
        )

        return cast(str, container.id)

    return _with_connection_retry(operation)


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
