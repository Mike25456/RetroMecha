"""
Instala retromecha_listener.py en la carpeta scripts de Maya y lo enlaza en userSetup.py.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from launcher.paths import PROJECT_ROOT

LISTENER_SOURCE = Path(__file__).resolve().parent / "maya_listener.py"
USERSETUP_BEGIN = "# <<< RetroMecha listener BEGIN (no borrar) >>>"
USERSETUP_END = "# <<< RetroMecha listener END >>>"
USERSETUP_IMPORT = (
    "try:\n"
    "    import retromecha_listener  # noqa: F401\n"
    "except Exception as _rm_err:\n"
    "    import maya.cmds as _rm_mc\n"
    "    _rm_mc.warning('[RetroMecha] Listener: ' + str(_rm_err))\n"
)


def maya_version_from_exe(maya_exe: Path) -> str:
    m = re.search(r"Maya(\d{4})", maya_exe.as_posix(), re.I)
    if m:
        return m.group(1)
    return "2025"


def maya_scripts_dir(maya_exe: Path) -> Path:
    version = maya_version_from_exe(maya_exe)
    return Path.home() / "Documents" / "maya" / version / "scripts"


def install_listener(maya_exe: Path) -> Path:
    """
    Copia el listener a ~/Documents/maya/<ver>/scripts/ y actualiza userSetup.py.
    Returns: carpeta scripts de Maya.
    """
    scripts = maya_scripts_dir(maya_exe)
    scripts.mkdir(parents=True, exist_ok=True)

    dest = scripts / "retromecha_listener.py"
    shutil.copy2(LISTENER_SOURCE, dest)

    user_setup = scripts / "userSetup.py"
    block = f"{USERSETUP_BEGIN}\n{USERSETUP_IMPORT}{USERSETUP_END}\n"
    if user_setup.is_file():
        text = user_setup.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"{re.escape(USERSETUP_BEGIN)}.*?{re.escape(USERSETUP_END)}\n?",
            re.S,
        )
        if pattern.search(text):
            user_setup.write_text(pattern.sub(block, text), encoding="utf-8")
        elif "retromecha_listener" not in text:
            with open(user_setup, "a", encoding="utf-8") as f:
                f.write(f"\n{block}")
    else:
        user_setup.write_text(block, encoding="utf-8")

    return scripts


def install_in_running_maya_script() -> Path:
    """Script de una sola vez para pegar en Script Editor si Maya ya estaba abierto."""
    return PROJECT_ROOT / "launcher" / "install_in_running_maya.py"
