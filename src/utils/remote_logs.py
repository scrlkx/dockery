import json
import os
import select
import shlex
import shutil
import sys
from typing import Any, cast

import paramiko

from .connection_profile import ConnectionProfile
from .remote_console import open_ssh_clients


def _run_logs(profile: ConnectionProfile, container_id: str, tail: int) -> int:
    ssh_client, jump_client = open_ssh_clients(profile)

    try:
        transport = ssh_client.get_transport()

        if transport is None:
            raise RuntimeError("SSH transport is not available")

        channel: paramiko.Channel = transport.open_session()
        size = shutil.get_terminal_size((80, 24))
        term = os.environ.get("TERM", "xterm-256color")
        channel.get_pty(term=term, width=size.columns, height=size.lines)

        command = shlex.join(
            [
                "docker",
                "logs",
                "--tail",
                str(tail),
                "-f",
                container_id,
            ]
        )
        channel.exec_command(command)

        stdout = sys.stdout.buffer

        while True:
            ready, _, _ = select.select([cast(Any, channel)], [], [], 0.1)

            if channel in ready:
                if channel.recv_ready():
                    stdout.write(channel.recv(4096))
                    stdout.flush()

                if channel.recv_stderr_ready():
                    stdout.write(channel.recv_stderr(4096))
                    stdout.flush()

            if channel.exit_status_ready() and not (
                channel.recv_ready() or channel.recv_stderr_ready()
            ):
                break

        return channel.recv_exit_status()
    finally:
        ssh_client.close()

        if jump_client is not None:
            jump_client.close()


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: remote_logs <profile-json> <container-id> <tail>", file=sys.stderr
        )
        return 2

    profile = cast(ConnectionProfile, json.loads(sys.argv[1]))
    container_id = sys.argv[2]
    tail = int(sys.argv[3])

    try:
        return _run_logs(profile, container_id, tail)
    except Exception as exception:
        print(str(exception), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
