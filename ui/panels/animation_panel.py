"""ANIMACIONES section of the RetroMecha UI."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

import ui.theme as T
from ui import scene_utils as sc, state
from animations.registry import list_animations, get_animation


_current_anim = [None]


def build(wrapped=True):
    if wrapped:
        mc.frameLayout(
            label='  >  ANIMACIONES',
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            backgroundColor=T.PANEL,
            marginHeight=6, marginWidth=6,
        )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    anims = list_animations()
    _current_anim[0] = anims[0] if anims else None

    if anims:
        mc.rowLayout(nc=2, cw2=[128, 140],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label='Animación', align='right', font='smallPlainLabelFont')
        mc.optionMenu(
            changeCommand=lambda val: _current_anim.__setitem__(0, val),
            annotation='Selecciona una animación para aplicar al mecha',
        )
        for name in anims:
            mc.menuItem(label=name)
        mc.setParent('..')

        mc.rowLayout(nc=2, cw2=[134, 134],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[3, 3])
        mc.button(label='Aplicar', h=28,
                  backgroundColor=T.CYAN,
                  command=_apply_animation,
                  annotation='Aplica la animación seleccionada al mecha')
        mc.button(label='Eliminar', h=28,
                  backgroundColor=T.SLATE,
                  command=_remove_animation,
                  annotation='Elimina la animación actual del mecha')
        mc.setParent('..')
    else:
        mc.text(label='(no hay animaciones registradas)',
                align='left', font='smallPlainLabelFont')

    mc.separator(h=4, style='none')
    mc.setParent('..')
    if wrapped:
        mc.setParent('..')


def _apply_animation(*_):
    mecha_root = sc.find_mecha_group()
    if not mecha_root:
        print('[RetroMecha][Anim] No hay mecha en escena')
        return
    anim_cls = get_animation(_current_anim[0])
    if not anim_cls:
        print(f'[RetroMecha][Anim] Animacion "{_current_anim[0]}" no encontrada')
        return
    anim = anim_cls(mecha_root)
    anim.apply()


def _remove_animation(*_):
    mecha_root = sc.find_mecha_group()
    if not mecha_root:
        print('[RetroMecha][Anim] No hay mecha en escena')
        return
    anim_cls = get_animation(_current_anim[0])
    if not anim_cls:
        return
    anim = anim_cls(mecha_root)
    anim.remove()


def apply_animation_quick(name):
    """Aplica animación por nombre directamente (modo Rápido/Pro)."""
    state._ACTIVE_ANIM[0] = name
    mecha_root = sc.find_mecha_group()
    if not mecha_root:
        print('[RetroMecha][Anim] No hay mecha en escena')
        return
    anim_cls = get_animation(name)
    if not anim_cls:
        print(f'[RetroMecha][Anim] Animacion "{name}" no encontrada')
        return
    anim = anim_cls(mecha_root)
    anim.apply()
    try:
        mc.play(forward=True)
    except Exception:
        pass


def remove_animation_quick():
    """Remueve animación sin depender de optionMenu (modo Rápido)."""
    sc.clean_animations()
    print('[RetroMecha][Anim] Animaciones removidas')
