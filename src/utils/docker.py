from typing import Any, Iterable, Optional

from docker.models.containers import Container

from ..client import get_docker_client


def get_container_attribute(
    container: Container, attribute: str, default: Optional[Any] = None
) -> Optional[Any]:
    keys = attribute.split(".")

    attrs = container.attrs
    current = attrs

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def get_container_created_at(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    original = get_container_attribute(container, "Created")

    return original if original else default


def get_container_started_at(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    original = get_container_attribute(container, "State.StartedAt")

    return original if original else default


def get_container_image(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    return (
        container.image.tags[0]
        if container.image and len(container.image.tags) > 0
        else default
    )


def get_container_cmd(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    cmd = get_container_attribute(container, "Config.Cmd")

    if cmd and isinstance(cmd, str):
        return cmd

    if cmd and isinstance(cmd, list):
        return " ".join(cmd)

    return default


def get_container_entrypoint(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    entrypoint = get_container_attribute(container, "Config.Entrypoint")

    if entrypoint and isinstance(entrypoint, str):
        return entrypoint

    if entrypoint and isinstance(entrypoint, list):
        return " ".join(entrypoint)

    return default


def get_container_restart_policy(
    container: Container, default: Optional[str] = None
) -> Optional[str]:
    policy = get_container_attribute(container, "HostConfig.RestartPolicy")

    if policy:
        return policy.get("Name")

    return default


def get_container_environment_variables(
    container: Container,
) -> dict[str, str]:
    env = get_container_attribute(container, "Config.Env", [])

    if not isinstance(env, Iterable):
        return {}

    variables: dict[str, str] = {}

    for item in env:
        if not isinstance(item, str):
            continue

        # split only on first "="
        key, sep, value = item.partition("=")
        if not sep:
            continue

        variables[key] = value

    return variables


def get_container_networks(
    container: Container,
) -> dict[str, str]:
    net = get_container_attribute(container, "NetworkSettings.Networks", [])

    if not isinstance(net, Iterable):
        return {}

    networks: dict[str, str] = {}

    for key, item in net.items():  # type: ignore[attr-defined]
        networks[key] = item.get("IPAddress", "-")

    return networks


def get_container_ports(
    container: Container,
) -> dict[str, str]:
    bindings = get_container_attribute(container, "HostConfig.PortBindings", [])

    if not isinstance(bindings, Iterable):
        return {}

    ports: dict[str, str] = {}

    for key, item in bindings.items():  # type: ignore[attr-defined]
        ports[key] = ", ".join(list(map(lambda binding: binding.get("HostPort"), item)))

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
    container = get_docker_client().containers.get(name)
    container.start()


def stop_container(name: str) -> None:
    container = get_docker_client().containers.get(name)
    container.stop()


def pause_container(name: str) -> None:
    container = get_docker_client().containers.get(name)
    container.pause()


def unpause_container(name: str) -> None:
    container = get_docker_client().containers.get(name)
    container.unpause()


def restart_container(name: str) -> None:
    container = get_docker_client().containers.get(name)
    container.restart()


def kill_container(name: str) -> None:
    container = get_docker_client().containers.get(name)
    container.kill()


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

    return actions.get(container.status, [])


def get_container_volumes(
    container: Container,
) -> dict[str, str]:
    mounts = get_container_attribute(container, "Mounts", [])

    if not isinstance(mounts, Iterable):
        return {}

    volumes: dict[str, str] = {}

    for item in mounts:
        name = item.get("Name") or item.get("Source")
        mode = item.get("Mode")

        volumes[name] = mode

    return volumes
