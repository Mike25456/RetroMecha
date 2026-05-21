"""Al iniciar Maya: deja :7001 en MEL (como el rig)."""

import maya.cmds as mc
import maya.utils


def _open_port():
    if not mc.commandPort(":7001", query=True, exists=True):
        mc.commandPort(name=":7001", sourceType="mel", closeOnDisconnect=False)
        print("[RetroMecha] commandPort :7001 (mel) listo")


maya.utils.executeDeferred(_open_port)
