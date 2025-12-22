from functools import lru_cache

import docker
from docker import DockerClient


@lru_cache(maxsize=1)
def get_docker_client() -> DockerClient:
    return docker.from_env()
