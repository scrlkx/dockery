import logging
import os
from typing import Any

import paramiko
from docker.transport.sshconn import SSHHTTPAdapter

from .connection_profile import ConnectionProfile, build_ssh_uri


class DockerySSHAdapter(SSHHTTPAdapter):
    def __init__(
        self,
        profile: ConnectionProfile,
        timeout: int = 60,
        pool_connections: int = 1,
        max_pool_size: int = 10,
    ) -> None:
        self._profile = profile
        self._jump_client: paramiko.SSHClient | None = None

        base_url = build_ssh_uri(profile)

        super().__init__(
            base_url,
            timeout=timeout,
            pool_connections=pool_connections,
            max_pool_size=max_pool_size,
            shell_out=False,
        )

    def _create_paramiko_client(self, base_url: str) -> None:
        logging.getLogger("paramiko").setLevel(logging.WARNING)

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.WarningPolicy())

        profile = self._profile

        self.ssh_params: dict[str, Any] = {
            "hostname": profile.get("host", "localhost"),
            "port": profile.get("port", 22),
            "username": profile.get("user"),
            "allow_agent": True,
            "look_for_keys": True,
        }

        identity_file = profile.get("identity_file")

        if identity_file:
            self.ssh_params["key_filename"] = os.path.expanduser(identity_file)

        jump_host = profile.get("jump_host")

        if jump_host:
            self._jump_client = paramiko.SSHClient()
            self._jump_client.load_system_host_keys()
            self._jump_client.set_missing_host_key_policy(paramiko.WarningPolicy())

            jump_params: dict[str, Any] = {
                "hostname": jump_host,
                "port": profile.get("jump_port", 22),
                "username": profile.get("jump_user"),
                "allow_agent": True,
                "look_for_keys": True,
            }

            jump_identity = profile.get("jump_identity_file")

            if jump_identity:
                jump_params["key_filename"] = os.path.expanduser(jump_identity)

            self._jump_client.connect(**jump_params)

            transport = self._jump_client.get_transport()
            assert transport is not None

            dest_host = profile.get("host", "localhost")
            dest_port = profile.get("port", 22)

            channel = transport.open_channel(
                "direct-tcpip",
                (dest_host, dest_port),
                ("127.0.0.1", 0),
            )

            self.ssh_params["sock"] = channel

    def close(self) -> None:
        super().close()

        if self._jump_client:
            self._jump_client.close()
            self._jump_client = None
