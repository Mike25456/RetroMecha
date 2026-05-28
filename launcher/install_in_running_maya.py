"""Pegar en Script Editor (Python) si Maya ya estaba abierto."""

import os
import runpy
import maya.cmds as mc

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not mc.commandPort(":7001", query=True, exists=True):
    mc.commandPort(name=":7001", sourceType="mel", closeOnDisconnect=False)

runpy.run_path(os.path.join(_ROOT, "launcher", "bootstrap_in_maya.py"), run_name="__main__")
print("[RetroMecha] Listo. run_retromecha.py ya debería funcionar.")
