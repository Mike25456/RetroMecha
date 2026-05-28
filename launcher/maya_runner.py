"""Igual que launch_in_maya.py de rigs: MEL + commandPort, luego maya -command."""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path

from launcher.maya_install import install_listener
from launcher.maya_locator import find_maya_executable
from launcher.maya_process import is_maya_running
from launcher.paths import BOOTSTRAP_PY

# Puertos que escucha el rig (MEL). El listener también abre :7001 al iniciar Maya.
COMMAND_PORTS = [7001, 7002, 7003]


def build_maya_command(launcher_path: Path) -> str:
    p = str(launcher_path.resolve()).replace("\\", "\\\\")
    return (
        'python("import runpy; '
        f'_retromecha_bootstrap = runpy.run_path(r\\\"{p}\\\", '
        'run_name=\\\"__main__\\\")")'
    )


def send_to_running_maya(command: str) -> bool:
    payload = (command + ";\n").encode("utf-8")
    for port in COMMAND_PORTS:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.7) as sock:
                sock.sendall(payload)
                return True
        except OSError:
            continue
    return False


def run_retromecha() -> int:
    try:
        maya_exe = find_maya_executable()
    except RuntimeError as e:
        print(f"[RetroMecha] ERROR: {e}")
        return 1

    install_listener(maya_exe)
    maya_cmd = build_maya_command(BOOTSTRAP_PY)

    print(f"[RetroMecha] Maya: {maya_exe}")

    if send_to_running_maya(maya_cmd):
        print("[RetroMecha] Plugin enviado a Maya abierta (commandPort).")
        return 0

    if is_maya_running():
        print("[RetroMecha] Maya abierto pero sin commandPort.")
        print("  En Maya → Script Editor → MEL, pega y ejecuta:")
        print('  commandPort -name ":7001" -sourceType "mel";')
        print("  Luego vuelve a correr run_retromecha.py")
        print()
        print("  O una sola vez en Python:")
        script = BOOTSTRAP_PY.parent / "install_in_running_maya.py"
        print(f"  exec(open(r'{script.resolve()}', encoding='utf-8').read())")
        return 1

    subprocess.Popen([str(maya_exe), "-command", maya_cmd])
    print("[RetroMecha] Maya abierto con plugin (-command).")
    return 0
