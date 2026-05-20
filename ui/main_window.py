"""
RetroMecha — ui/main_window.py  v4
Una sola pestaña con secciones colapsables: MECHA y TERRENO.
Botones globales: Generar · Aleatorio · Resetear
Auto-rebuild al soltar slider (changeCommand).
"""

import random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

WIN_ID = 'RetroMechaWindow'
_SEED  = [None]

PRESET_MAP = {
    'Avanzada':         'avanzada',
    'Hangar':           'hangar',
    'Campo de batalla': 'campo_de_batalla',
    'Centinela':        'centinela',
}
TERRAIN_PATTERNS = [
    'RetroMecha_Scene_*',
    'rm_terrain_*', 'rm_ground_*', 'rm_monument_*',
    'rm_platform_*', 'rm_fragment_*', 'rm_debris_*',
    'rm_ramps_*', 'rm_pillars_*', 'rm_tower_*', 'rm_skyline_*',
]


# =============================================================================
#  PUNTO DE ENTRADA
# =============================================================================

def build_ui():
    if not MAYA_AVAILABLE:
        print('[RetroMecha] Ejecutar dentro de Maya')
        return

    if mc.window(WIN_ID, exists=True):
        mc.deleteUI(WIN_ID, window=True)

    win = mc.window(WIN_ID, title='RetroMecha v4',
                    sizeable=True, resizeToFitChildren=True,
                    minimizeButton=True, maximizeButton=False,
                    width=340)

    mc.scrollLayout(childResizable=True)
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    # =========================================================================
    #  HEADER + SEMILLA
    # =========================================================================
    mc.separator(h=8, style='none')
    mc.text(label='RETROMECHA — GENERADOR PROCEDURAL',
            font='boldLabelFont', align='center', h=28,
            backgroundColor=[0.12, 0.22, 0.30])
    mc.separator(h=6, style='in')

    mc.rowLayout(nc=2, cw2=[60, 260],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
    seed_field = mc.textField(placeholderText='dejar vacío = aleatoria',
                              editable=True)
    mc.setParent('..')
    mc.separator(h=8, style='none')

    # =========================================================================
    #  HELPERS
    # =========================================================================
    def fsl(label, mn, mx, val, step=0.01, prec=2, on_cc=None):
        """Float slider con label y changeCommand."""
        ctrl = mc.floatSliderGrp(
            label=label, field=True,
            min=mn, max=mx, value=val, step=step, precision=prec,
            columnWidth3=[128, 52, 128],
            columnAlign3=['right', 'left', 'left'],
        )
        if on_cc:
            mc.floatSliderGrp(ctrl, e=True, changeCommand=on_cc)
        return ctrl

    def isl(label, mn, mx, val, on_cc=None):
        """Int slider con label y changeCommand."""
        ctrl = mc.intSliderGrp(
            label=label, field=True,
            min=mn, max=mx, value=val,
            columnWidth3=[128, 52, 128],
            columnAlign3=['right', 'left', 'left'],
        )
        if on_cc:
            mc.intSliderGrp(ctrl, e=True, changeCommand=on_cc)
        return ctrl

    def resolve_seed() -> int:
        txt = mc.textField(seed_field, q=True, text=True).strip()
        if txt.isdigit():
            s = int(txt)
        else:
            s = random.randint(0, 99999)
            mc.textField(seed_field, e=True, text=str(s))
        _SEED[0] = s
        return s

    # =========================================================================
    #  SECCIÓN MECHA (colapsable)
    # =========================================================================
    mecha_frame = mc.frameLayout(
        label='  ▶  MECHA',
        collapsable=True, collapse=False,
        borderStyle='etchedIn',
        backgroundColor=[0.12, 0.22, 0.18],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    # — Callbacks mecha (definidos antes de los sliders) ——————————————————————
    def _on_mecha_cc(*_):
        _rebuild_mecha()

    # — Sliders mecha —————————————————————————————————————————————————————————
    sep_sl    = fsl('Separación',          0.10, 0.80,  0.35, on_cc=_on_mecha_cc)
    angle_sl  = fsl('Ángulos conectores',  0.0,  45.0,  15.0,
                    step=0.5, prec=1,      on_cc=_on_mecha_cc)
    aggr_sl   = fsl('Agresividad',         0.0,   1.0,   0.5, on_cc=_on_mecha_cc)
    decay_sl  = fsl('Decrecimiento',       0.50,  1.0,   0.85, on_cc=_on_mecha_cc)
    height_sl = fsl('Altura',              0.50,  2.0,   1.0,
                    step=0.05,             on_cc=_on_mecha_cc)

    mc.separator(h=4)
    sym_cb    = mc.checkBox(label='Simetría',
                            value=True,  changeCommand=_on_mecha_cc)
    panels_cb = mc.checkBox(label='Emplear Paneles',
                            value=True,  changeCommand=_on_mecha_cc)

    mc.separator(h=6)
    mc.button(label='Aleatorio Mecha', h=28,
              backgroundColor=[0.32, 0.18, 0.32],
              command=lambda *_: _random_mecha())

    mc.separator(h=4, style='none')
    mc.setParent('..')  # columnLayout
    mc.setParent('..')  # frameLayout mecha

    # =========================================================================
    #  SECCIÓN TERRENO (colapsable)
    # =========================================================================
    mc.separator(h=4, style='none')
    terrain_frame = mc.frameLayout(
        label='  ▶  TERRENO',
        collapsable=True, collapse=True,   # empieza colapsado
        borderStyle='etchedIn',
        backgroundColor=[0.14, 0.18, 0.28],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    # — Callbacks terreno ——————————————————————————————————————————————————————
    def _on_terrain_cc(*_):
        _rebuild_terrain_only()

    # — Preset dropdown ———————————————————————————————————————————————————————
    mc.rowLayout(nc=2, cw2=[130, 178],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset de escena', align='right',
            font='smallPlainLabelFont')
    preset_menu = mc.optionMenu(changeCommand=_on_terrain_cc)
    mc.menuItem(label='Avanzada')
    mc.menuItem(label='Hangar')
    mc.menuItem(label='Campo de batalla')
    mc.menuItem(label='Centinela')
    mc.setParent('..')

    mc.separator(h=4)

    # — Sliders terreno ————————————————————————————————————————————————————————
    t_mon_sl   = fsl('Escala monumento',   3.0,  9.0, 5.5,
                     step=0.1, on_cc=_on_terrain_cc)
    t_plat_sl  = isl('N° plataformas',     3,   16,   8, on_cc=_on_terrain_cc)
    t_frag_sl  = isl('N° fragmentos',      2,   24,  12, on_cc=_on_terrain_cc)
    t_deb_sl   = isl('Debris (piezas)',   20,  150,  80, on_cc=_on_terrain_cc)
    t_pil_sl   = isl('Pilares',            2,   16,   8, on_cc=_on_terrain_cc)
    t_ramp_sl  = fsl('Prob. rampas',       0.0,  1.0, 0.55, on_cc=_on_terrain_cc)
    t_ring_sl  = fsl('Radio máx. terreno', 8.0, 35.0, 22.0,
                     step=0.5, on_cc=_on_terrain_cc)

    mc.separator(h=6)
    mc.button(label='Aleatorio Terreno', h=28,
              backgroundColor=[0.18, 0.22, 0.36],
              command=lambda *_: _random_terrain())

    mc.separator(h=4, style='none')
    mc.setParent('..')  # columnLayout
    mc.setParent('..')  # frameLayout terreno

    # =========================================================================
    #  BOTONES GLOBALES + TOGGLE TERRENO
    # =========================================================================
    mc.separator(h=8, style='in')

    mc.rowLayout(nc=3, cw3=[107, 107, 107],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[3, 3, 3])

    mc.button(label='Generar',   h=38,
              backgroundColor=[0.18, 0.42, 0.22],
              command=lambda *_: _on_generar())
    mc.button(label='Aleatorio', h=38,
              backgroundColor=[0.40, 0.20, 0.38],
              command=lambda *_: _random_all())
    mc.button(label='Resetear',  h=38,
              backgroundColor=[0.40, 0.16, 0.16],
              command=lambda *_: _on_reset())
    mc.setParent('..')

    mc.separator(h=6, style='none')

    # =========================================================================
    #  MATERIALES (placeholder)
    # =========================================================================
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  ▶  MATERIALES  —  próxima fase',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.22, 0.18, 0.12],
        marginHeight=8, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)
    mc.text(label='Shaders retro-futuristas (Lambert / Blinn / PBR)',
            align='left', font='smallPlainLabelFont')
    mc.text(label='Paleta por preset: oxidado · pulido · mate',
            align='left', font='smallPlainLabelFont')
    mc.text(label='Asignación automática por módulo',
            align='left', font='smallPlainLabelFont')
    mc.setParent('..')
    mc.setParent('..')

    mc.separator(h=8, style='none')

    # =========================================================================
    #  FUNCIONES INTERNAS
    # =========================================================================

    def _collect_mecha() -> dict:
        return {
            'separation':      mc.floatSliderGrp(sep_sl,   q=True, value=True),
            'connector_angle': mc.floatSliderGrp(angle_sl, q=True, value=True),
            'aggressiveness':  mc.floatSliderGrp(aggr_sl,  q=True, value=True),
            'decay':           mc.floatSliderGrp(decay_sl, q=True, value=True),
            'height_scale':    mc.floatSliderGrp(height_sl,q=True, value=True),
            'symmetry':        mc.checkBox(sym_cb,   q=True, value=True),
            'use_panels':      mc.checkBox(panels_cb,q=True, value=True),
        }

    def _collect_terrain() -> dict:
        return {
            'monument_scale':   mc.floatSliderGrp(t_mon_sl,  q=True, value=True),
            'platform_count':   mc.intSliderGrp(t_plat_sl,   q=True, value=True),
            'fragment_count':   mc.intSliderGrp(t_frag_sl,   q=True, value=True),
            'debris_count':     mc.intSliderGrp(t_deb_sl,    q=True, value=True),
            'pillar_count':     mc.intSliderGrp(t_pil_sl,    q=True, value=True),
            'ramp_probability': mc.floatSliderGrp(t_ramp_sl, q=True, value=True),
            'ring_max_r':       mc.floatSliderGrp(t_ring_sl, q=True, value=True),
        }

    def _terrain_active() -> bool:
        """Siempre True — terreno incluido por defecto."""
        return True

    def _clean_mecha():
        for n in (mc.ls('RetroMecha_*', type='transform') or []):
            try: mc.delete(n)
            except: pass

    def _clean_terrain():
        for pat in TERRAIN_PATTERNS:
            for n in (mc.ls(pat, type='transform') or []):
                try: mc.delete(n)
                except: pass

    def _rebuild_mecha(*_):
        """Reconstruye solo el mecha. Si terreno visible, lo regenera también."""
        seed   = _SEED[0] if isinstance(_SEED[0], int) else resolve_seed()
        _SEED[0] = seed
        params = _collect_mecha()
        params['_seed'] = seed

        _clean_mecha()
        from core.mecha_builder import MechaBuilder
        grp = MechaBuilder(params, seed=seed).build()
        if grp and mc.objExists(grp):
            try:
                bb   = mc.exactWorldBoundingBox(grp)
                lift = 0.5 - bb[1]
                if abs(lift) > 0.01:
                    mc.move(0, lift, 0, grp, relative=True, worldSpace=True)
            except Exception:
                pass
            mc.select(grp)
            # Si terreno visible, actualizarlo también
            if _terrain_active():
                _rebuild_terrain_only()
            else:
                mc.viewFit()

    def _rebuild_terrain_only(*_):
        """Regenera el terreno usando el mecha que ya existe."""
        seed   = _SEED[0] if isinstance(_SEED[0], int) else resolve_seed()
        params = _collect_mecha()
        params['_seed'] = seed

        preset_label = mc.optionMenu(preset_menu, q=True, value=True)
        preset_name  = PRESET_MAP.get(preset_label, 'avanzada')
        overrides    = _collect_terrain()

        # Bbox del mecha existente
        mecha_grp  = next((n for n in (mc.ls('RetroMecha_*', type='transform') or [])
                           if 'Scene' not in n), None)
        mecha_bbox = (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)
        if mecha_grp and mc.objExists(mecha_grp):
            try:
                mecha_bbox = tuple(mc.exactWorldBoundingBox(mecha_grp))
            except Exception:
                pass

        _clean_terrain()

        from terrain.terrain_builder import TerrainBuilder
        tb = TerrainBuilder(params=params, seed=seed + 1000,
                            preset_name=preset_name, mecha_bbox=mecha_bbox)
        tb.preset.update(overrides)
        grp = tb.build()
        if grp and mc.objExists(grp):
            mc.select(grp)
            mc.viewFit()

    def _on_generar(*_):
        """Botón GENERAR: usa semilla actual y decide qué construir."""
        seed = resolve_seed()
        params = _collect_mecha()
        params['_seed'] = seed

        if _terrain_active():
            # Escena completa
            preset_label = mc.optionMenu(preset_menu, q=True, value=True)
            preset_name  = PRESET_MAP.get(preset_label, 'avanzada')
            overrides    = _collect_terrain()

            _clean_mecha()
            _clean_terrain()

            from terrain.scene_composer import SceneComposer
            import terrain.terrain_builder as tb_mod

            _orig = tb_mod.TerrainBuilder.__init__
            def _patch(self_tb, *a, **kw):
                _orig(self_tb, *a, **kw)
                self_tb.preset.update(overrides)
            tb_mod.TerrainBuilder.__init__ = _patch
            try:
                grp = SceneComposer(params, seed=seed,
                                    terrain_preset=preset_name).compose()
            finally:
                tb_mod.TerrainBuilder.__init__ = _orig

            if grp and mc.objExists(grp):
                mc.select(grp)
                mc.viewFit()
        else:
            # Solo mecha
            _clean_mecha()
            from core.mecha_builder import MechaBuilder
            grp = MechaBuilder(params, seed=seed).build()
            if grp and mc.objExists(grp):
                try:
                    bb   = mc.exactWorldBoundingBox(grp)
                    lift = 0.5 - bb[1]
                    if abs(lift) > 0.01:
                        mc.move(0, lift, 0, grp, relative=True, worldSpace=True)
                except Exception:
                    pass
                mc.select(grp)
                mc.viewFit()

    def _random_mecha(*_):
        """Aleatoriza sliders del mecha y reconstruye."""
        mc.floatSliderGrp(sep_sl,   e=True, value=random.uniform(0.10, 0.80))
        mc.floatSliderGrp(angle_sl, e=True, value=random.uniform(0.0,  45.0))
        mc.floatSliderGrp(aggr_sl,  e=True, value=random.uniform(0.0,   1.0))
        mc.floatSliderGrp(decay_sl, e=True, value=random.uniform(0.50,  1.0))
        mc.floatSliderGrp(height_sl,e=True, value=random.uniform(0.50,  2.0))
        mc.checkBox(sym_cb, e=True, value=random.choice([True, False]))
        _SEED[0] = random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(_SEED[0]))
        _rebuild_mecha()

    def _random_terrain(*_):
        """Aleatoriza sliders del terreno y reconstruye solo el terreno."""
        mc.floatSliderGrp(t_mon_sl, e=True, value=random.uniform(3.0,  9.0))
        mc.intSliderGrp(t_plat_sl,  e=True, value=random.randint(3,   16))
        mc.intSliderGrp(t_frag_sl,  e=True, value=random.randint(2,   24))
        mc.intSliderGrp(t_deb_sl,   e=True, value=random.randint(20, 150))
        mc.intSliderGrp(t_pil_sl,   e=True, value=random.randint(2,   16))
        mc.floatSliderGrp(t_ramp_sl,e=True, value=random.uniform(0.0,  1.0))
        mc.floatSliderGrp(t_ring_sl,e=True, value=random.uniform(10.0,35.0))
        _rebuild_terrain_only()

    def _random_all(*_):
        """Aleatoriza TODO y genera escena completa."""
        _random_mecha()
        if _terrain_active():
            _random_terrain()

    def _on_reset(*_):
        _clean_mecha()
        _clean_terrain()
        mc.textField(seed_field, e=True, text='')
        _SEED[0] = None
        print('[RetroMecha] Escena limpiada')

    mc.showWindow(win)
    print('[RetroMecha] UI v4 abierta')