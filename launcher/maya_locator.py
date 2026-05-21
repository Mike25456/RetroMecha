"""
Localiza maya.exe en Windows (registro Autodesk, rutas habituales, config local).
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from launcher.paths import LOCAL_CONFIG, PROJECT_ROOT

# Puertos usados para inyectar Python si -script no alcanza la sesión abierta
COMMAND_PORT = 7722


def _load_local_config() -> dict:
    if not LOCAL_CONFIG.is_file():
        return {}
    try:
        with open(LOCAL_CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[RetroMecha] Aviso: no se pudo leer {LOCAL_CONFIG.name}: {e}")
        return {}


def _normalize_exe(path: str | Path) -> Path | None:
    p = Path(path)
    if p.is_file() and p.name.lower() in ("maya.exe", "maya"):
        return p.resolve()
    if p.is_dir():
        candidate = p / "bin" / "maya.exe"
        if candidate.is_file():
            return candidate.resolve()
    return None


def _registry_maya_paths() -> list[Path]:
    """Lee InstallPath desde el registro de Windows (Autodesk Maya)."""
    try:
        import winreg
    except ImportError:
        return []

    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Autodesk\Maya"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Autodesk\Maya"),
    ]
    found: list[Path] = []
    version_re = re.compile(r"^\d{4}$")

    for hive, key_path in roots:
        try:
            with winreg.OpenKey(hive, key_path) as maya_key:
                i = 0
                while True:
                    try:
                        version = winreg.EnumKey(maya_key, i)
                        i += 1
                        if not version_re.match(version):
                            continue
                        with winreg.OpenKey(maya_key, version) as ver_key:
                            try:
                                with winreg.OpenKey(ver_key, "Setup") as setup_key:
                                    install_path, _ = winreg.QueryValueEx(
                                        setup_key, "InstallPath"
                                    )
                                    exe = _normalize_exe(install_path)
                                    if exe:
                                        found.append(exe)
                            except OSError:
                                pass
                    except OSError:
                        break
        except OSError:
            continue

    return found


def _common_install_paths() -> list[Path]:
    bases = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    years = range(2030, 2018, -1)
    candidates: list[Path] = []
    for base in bases:
        autodesk = base / "Autodesk"
        if not autodesk.is_dir():
            continue
        for year in years:
            candidates.append(autodesk / f"Maya{year}" / "bin" / "maya.exe")
    return [p for p in candidates if p.is_file()]


def _path_maya() -> list[Path]:
    """Detecta maya.exe si Autodesk/Maya fue agregado al PATH del sistema."""
    found = []
    for exe_name in ("maya.exe", "maya"):
        path = shutil.which(exe_name)
        if path:
            exe = _normalize_exe(path)
            if exe:
                found.append(exe)
    return found


def find_maya_executable(preferred_version: str | None = None) -> Path:
    """
    Devuelve la ruta a maya.exe o lanza RuntimeError con instrucciones.
    """
    cfg = _load_local_config()
    custom = cfg.get("maya_executable") or os.environ.get("RETROMECHA_MAYA_EXE")
    if custom:
        exe = _normalize_exe(custom)
        if exe:
            return exe

    maya_location = os.environ.get("MAYA_LOCATION")
    if maya_location:
        exe = _normalize_exe(maya_location)
        if exe:
            return exe

    version = preferred_version or cfg.get("maya_version")
    collected: list[Path] = []
    collected.extend(_registry_maya_paths())
    collected.extend(_path_maya())
    collected.extend(_common_install_paths())

    # Quitar duplicados preservando orden (más reciente primero en registry)
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in collected:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    if version:
        ver = str(version)
        for p in unique:
            if ver in p.as_posix():
                return p

    if unique:
        return unique[0]

    example = PROJECT_ROOT / "retromecha.local.json.example"
    raise RuntimeError(
        "No se encontró maya.exe.\n"
        "  • Instala Autodesk Maya, o\n"
        f"  • Copia {example.name} → retromecha.local.json y define maya_executable"
    )
