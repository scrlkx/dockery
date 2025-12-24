from functools import lru_cache

from docker import DockerClient, from_env


@lru_cache(maxsize=1)
def get_docker_client() -> DockerClient:
    return from_env()
