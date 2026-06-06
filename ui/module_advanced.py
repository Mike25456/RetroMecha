"""Carga specs y utilidades para paneles de configuracion avanzada por modulo."""

from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config' / 'module_advanced.json'
_CACHE: dict | None = None


def _load_all() -> dict:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    try:
        with open(_CONFIG_PATH, encoding='utf-8') as f:
            data = json.load(f)
        _CACHE = {
            k: v for k, v in data.items()
            if not k.startswith('_') and isinstance(v, dict)
        }
    except Exception as e:
        print(f'[RetroMecha] module_advanced.json: {e}')
        _CACHE = {}
    return _CACHE


def get_module_spec(module_key: str) -> dict | None:
    return _load_all().get(module_key)


def get_slider_specs(module_key: str) -> list[dict]:
    spec = get_module_spec(module_key)
    if not spec:
        return []
    sliders = spec.get('sliders', [])
    return [s for s in sliders if isinstance(s, dict) and s.get('key')]
