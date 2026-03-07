import getpass
import json
import os
import select
import shlex
import shutil
import signal
import sys
import termios
import tty
from typing import Any

import paramiko
from paramiko.ssh_exception import AuthenticationException

try:
    from .connection_profile import ConnectionProfile
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from connection_profile import ConnectionProfile


def _connect_client(
    profile: ConnectionProfile,
    *,
    jump_channel: paramiko.Channel | None = None,
    is_jump: bool = False,
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()

    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    prefix = "jump_" if is_jump else ""

    params: dict[str, Any] = {
        "hostname": profile.get(f"{prefix}host", "localhost"),
        "port": profile.get(f"{prefix}port", 22),
        "username": profile.get(f"{prefix}user"),
        "allow_agent": True,
        "look_for_keys": True,
    }

    identity_file = profile.get(f"{prefix}identity_file")

    if identity_file:
        params["key_filename"] = os.path.expanduser(identity_file)

    if jump_channel is not None:
        params["sock"] = jump_channel

    try:
        client.connect(**params)
        return client
    except AuthenticationException:
        if not sys.stdin.isatty():
            raise

        target = params["hostname"]
        username = params.get("username")
        prompt_target = f"{username}@{target}" if username else str(target)
        password = getpass.getpass(f"Password for {prompt_target}: ")

        params["password"] = password

        client.connect(**params)

        return client


def _open_ssh_clients(
    profile: ConnectionProfile,
) -> tuple[paramiko.SSHClient, paramiko.SSHClient | None]:
    jump_host = profile.get("jump_host")

    if not jump_host:
        return _connect_client(profile), None

    jump_client = _connect_client(profile, is_jump=True)
    transport = jump_client.get_transport()

    if transport is None:
        raise RuntimeError("Jump host transport is not available")

    channel = transport.open_channel(
        "direct-tcpip",
        (profile.get("host", "localhost"), profile.get("port", 22)),
        ("127.0.0.1", 0),
    )

    return _connect_client(profile, jump_channel=channel), jump_client


def _update_pty_size(channel: paramiko.Channel) -> None:
    size = shutil.get_terminal_size((80, 24))
    channel.resize_pty(width=size.columns, height=size.lines)


def _run_console(profile: ConnectionProfile, container_id: str) -> int:
    ssh_client, jump_client = _open_ssh_clients(profile)

    try:
        transport = ssh_client.get_transport()

        if transport is None:
            raise RuntimeError("SSH transport is not available")

        channel = transport.open_session()
        size = shutil.get_terminal_size((80, 24))
        term = os.environ.get("TERM", "xterm-256color")
        channel.get_pty(term=term, width=size.columns, height=size.lines)

        def on_resize(_signum: int, _frame: Any) -> None:
            _update_pty_size(channel)

        previous_handler = signal.getsignal(signal.SIGWINCH)
        signal.signal(signal.SIGWINCH, on_resize)

        docker_exec_args = [
            "docker",
            "exec",
            "-it",
        ]

        docker_exec_env = {
            "TERM": term,
            "COLORTERM": os.environ.get("COLORTERM"),
        }

        for key, value in docker_exec_env.items():
            if value:
                docker_exec_args.extend(["-e", f"{key}={value}"])

        docker_exec_args.extend([container_id, "/bin/sh"])
        command = shlex.join(docker_exec_args)
        channel.exec_command(command)

        stdin_fd = sys.stdin.fileno()
        stdout = sys.stdout.buffer
        old_tty = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)

        try:
            while True:
                read_list: list[Any] = [channel]

                if not channel.closed and not channel.exit_status_ready():
                    read_list.append(stdin_fd)

                ready, _, _ = select.select(read_list, [], [], 0.1)

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

                if stdin_fd in ready:
                    data = os.read(stdin_fd, 4096)

                    if not data:
                        channel.shutdown_write()
                    else:
                        channel.sendall(data)
        finally:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_tty)
            signal.signal(signal.SIGWINCH, previous_handler)

        return channel.recv_exit_status()
    finally:
        ssh_client.close()

        if jump_client is not None:
            jump_client.close()


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: remote_console <profile-json> <container-id>", file=sys.stderr)
        return 2

    profile = json.loads(sys.argv[1])
    container_id = sys.argv[2]

    try:
        return _run_console(profile, container_id)
    except Exception as exception:
        print(str(exception), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
