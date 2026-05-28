"""Al iniciar Maya: abre el puerto :7001 en MEL (como el rig)."""

import maya.cmds as mc
import maya.utils


def _open_port():
    try:
        mc.commandPort(name=':7001', sourceType='mel', closeOnDisconnect=False)
        print('[RetroMecha] commandPort :7001 (mel) listo')
    except Exception as e:
        if 'already in use' not in str(e).lower() and 'already exists' not in str(e).lower():
            print(f'[RetroMecha] commandPort: {e}')


maya.utils.executeDeferred(_open_port)
