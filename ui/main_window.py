"""
RetroMecha — ui/main_window.py
Ventana principal en Maya — replica el wireframe del documento técnico.
Tabs: Mecha (parámetros generativos) | Materiales (placeholder para siguiente fase)
"""

import random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print('[RetroMecha][UI] Maya no disponible')

WINDOW_ID   = 'RetroMechaWindow'
_LAST_SEED  = [None]   # estado mutable de sesión


# ── Punto de entrada ──────────────────────────────────────────────────────────

def build_ui():
    """Construye y muestra la ventana de RetroMecha."""
    if not MAYA_AVAILABLE:
        print('[RetroMecha] Ejecutar dentro de Maya')
        return

    # Destruir ventana previa si existe
    if mc.window(WINDOW_ID, exists=True):
        mc.deleteUI(WINDOW_ID, window=True)

    win = mc.window(
        WINDOW_ID,
        title='RetroMecha',
        sizeable=True,
        resizeToFitChildren=True,
        minimizeButton=True,
        maximizeButton=False,
        width=310,
    )

    # ── Layout raíz ───────────────────────────────────────────────────────────
    root_col = mc.columnLayout(adjustableColumn=True)

    tabs = mc.tabLayout(
        innerMarginWidth=10,
        innerMarginHeight=10,
        parent=root_col
    )

    # ═════════════════════════════ TAB: MECHA ════════════════════════════════
    mecha_col = mc.columnLayout(
        adjustableColumn=True,
        rowSpacing=5,
        parent=tabs
    )

    mc.separator(h=6, style='none')

    # -- Sliders --------------------------------------------------------------
    def slider(label, mn, mx, val, step=0.01, prec=2):
        mc.text(label=label, align='left', font='smallPlainLabelFont')
        return mc.floatSliderGrp(
            min=mn, max=mx, value=val, step=step,
            field=True, precision=prec,
            columnWidth3=[110, 52, 138],
            columnAlign3=['left', 'left', 'left'],
        )

    sep_sl    = slider('Separación',          0.10, 0.80, 0.35)
    angle_sl  = slider('Ángulos conectores',  0.0,  45.0, 15.0,  step=0.5,  prec=1)
    aggr_sl   = slider('Agresividad',         0.0,   1.0,  0.5)
    decay_sl  = slider('Decrecimiento',       0.50,  1.0,  0.85)
    height_sl = slider('Altura proporcional', 0.50,  2.0,  1.0,  step=0.05)

    mc.separator(h=8)

    # -- Checkboxes -----------------------------------------------------------
    sym_cb    = mc.checkBox(label='Simetría',            value=True)
    panels_cb = mc.checkBox(label='Emplear Paneles',     value=True)

    mc.separator(h=8)

    # -- Semilla --------------------------------------------------------------
    mc.text(label='Semilla', align='left', font='smallPlainLabelFont')
    seed_field = mc.textField(
        placeholderText='— semilla generada —',
        editable=True,    # permite fijar una semilla manualmente
        width=290,
    )

    mc.separator(h=10)

    # -- Botones --------------------------------------------------------------
    btn_row = mc.rowLayout(
        numberOfColumns=2,
        columnWidth2=[145, 145],
        columnAttach2=['both', 'both'],
        columnOffset2=[0, 4],
    )

    def _collect_params():
        return {
            'separation':      mc.floatSliderGrp(sep_sl,    q=True, value=True),
            'connector_angle': mc.floatSliderGrp(angle_sl,  q=True, value=True),
            'aggressiveness':  mc.floatSliderGrp(aggr_sl,   q=True, value=True),
            'decay':           mc.floatSliderGrp(decay_sl,  q=True, value=True),
            'height_scale':    mc.floatSliderGrp(height_sl, q=True, value=True),
            'symmetry':        mc.checkBox(sym_cb,    q=True, value=True),
            'use_panels':      mc.checkBox(panels_cb, q=True, value=True),
        }

    def on_generate(*_):
        # Leer semilla: manual si el campo tiene contenido, aleatoria si no
        seed_txt = mc.textField(seed_field, q=True, text=True).strip()
        if seed_txt.isdigit():
            seed = int(seed_txt)
        else:
            seed = random.randint(0, 99999)
            mc.textField(seed_field, e=True, text=str(seed))

        _LAST_SEED[0] = seed
        params = _collect_params()
        params['_seed'] = seed

        from core.mecha_builder import MechaBuilder
        builder = MechaBuilder(params, seed=seed)
        result  = builder.build()

        if result:
            mc.select(result)
            mc.viewFit()

    def on_reset(*_):
        # Elimina todos los grupos RetroMecha de la escena
        existing = mc.ls('RetroMecha_*', type='transform') or []
        if existing:
            mc.delete(existing)
            print(f'[RetroMecha] Eliminados: {existing}')
        mc.textField(seed_field, e=True, text='')
        _LAST_SEED[0] = None

    mc.button(
        label='Generar Mecha',
        command=on_generate,
        backgroundColor=[0.22, 0.22, 0.22],
        height=32,
    )
    mc.button(
        label='Resetear',
        command=on_reset,
        backgroundColor=[0.28, 0.18, 0.18],
        height=32,
    )
    mc.setParent('..')     # salir de btn_row
    mc.setParent(tabs)

    # ═════════════════════════════ TAB: MATERIALES ═══════════════════════════
    mat_col = mc.columnLayout(
        adjustableColumn=True,
        rowSpacing=6,
        parent=tabs
    )
    mc.separator(h=12, style='none')
    mc.text(label='Materiales — próxima fase', align='center',
            font='boldLabelFont')
    mc.separator(h=8)
    mc.text(label='Aquí se configurarán:', align='center')
    mc.text(label='• Shaders retro-futuristas (Lambert / Blinn)',  align='left')
    mc.text(label='• Paleta por preset (oxidado / pulido / mate)', align='left')
    mc.text(label='• Asignación automática por módulo',            align='left')
    mc.separator(h=12, style='none')
    mc.setParent(tabs)

    # ── Asignar labels a los tabs ─────────────────────────────────────────────
    mc.tabLayout(tabs, edit=True, tabLabel=[
        (mecha_col, 'Mecha'),
        (mat_col,   'Materiales'),
    ])

    mc.showWindow(win)
    print('[RetroMecha] UI abierta')
