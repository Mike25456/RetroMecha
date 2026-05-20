"""
RetroMecha — ui/main_window.py  v3
3 tabs: Mecha | Terreno | Materiales
Live-rebuild por tab al arrastrar sliders (patrón VehicleProcedural).

Patrón de referencia (ANiMAKo):
  cc  = change-complete (al soltar)  → _on_mecha_event / _on_terrain_event
  dc  = drag-command (al arrastrar)  → _on_mecha_live  / _on_terrain_live
  Auto-reconstruir  → reconstruye al soltar
  Live (arrastrar)  → reconstruye mientras se arrastra
"""

import random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

WIN_ID     = 'RetroMechaWindow'
_SEED      = [None]   # semilla activa
_MECHA_GRP = [None]   # último grupo de mecha generado

PRESET_MAP = {
    'Avanzada':         'avanzada',
    'Hangar':           'hangar',
    'Campo de batalla': 'campo_de_batalla',
    'Centinela':        'centinela',
}
TERRAIN_PATTERNS = [
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

    win = mc.window(WIN_ID, title='RetroMecha', sizeable=True,
                    resizeToFitChildren=True,
                    minimizeButton=True, maximizeButton=False,
                    width=340)

    root = mc.columnLayout(adjustableColumn=True)
    tabs = mc.tabLayout(innerMarginWidth=10, innerMarginHeight=10,
                        parent=root)

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 1 — MECHA
    # ──────────────────────────────────────────────────────────────────────────
    mecha_col = mc.columnLayout(adjustableColumn=True,
                                rowSpacing=4, parent=tabs)
    mc.separator(h=6, style='none')

    # ─ Helpers de slider con cc / dc ─────────────────────────────────────────
    def fslider(label, mn, mx, val, step=0.01, prec=2,
                on_cc=None, on_dc=None):
        mc.text(label=label, align='left', font='smallPlainLabelFont')
        kw = dict(min=mn, max=mx, value=val, step=step, field=True,
                  precision=prec,
                  columnWidth3=[120, 52, 150],
                  columnAlign3=['left', 'left', 'left'])
        if on_cc: kw['changeCommand']   = on_cc
        if on_dc: kw['dragCommand']     = on_dc
        return mc.floatSliderGrp(**kw)

    # Checkboxes live / auto (declarados antes de los sliders para el closure)
    mc.text(label='Reconstrucción automática', align='left',
            font='smallPlainLabelFont')
    m_row_live = mc.rowLayout(nc=2, cw2=[155, 155])
    m_auto_cb  = mc.checkBox(label='Auto (al soltar)', value=True)
    m_live_cb  = mc.checkBox(label='Live (arrastrar)', value=False)
    mc.setParent('..')
    mc.separator(h=6)

    # Callbacks que leen los checkboxes
    def _on_mecha_event(*_):
        if mc.checkBox(m_auto_cb, q=True, v=True):
            _rebuild_mecha()

    def _on_mecha_live(*_):
        if mc.checkBox(m_live_cb, q=True, v=True):
            _rebuild_mecha()

    # Sliders con callbacks inyectados
    sep_sl    = fslider('Separación',          0.10, 0.80,  0.35,
                        on_cc=_on_mecha_event, on_dc=_on_mecha_live)
    angle_sl  = fslider('Ángulos conectores',  0.0,  45.0,  15.0,
                        step=0.5, prec=1,
                        on_cc=_on_mecha_event, on_dc=_on_mecha_live)
    aggr_sl   = fslider('Agresividad',         0.0,   1.0,   0.5,
                        on_cc=_on_mecha_event, on_dc=_on_mecha_live)
    decay_sl  = fslider('Decrecimiento',       0.50,  1.0,   0.85,
                        on_cc=_on_mecha_event, on_dc=_on_mecha_live)
    height_sl = fslider('Altura proporcional', 0.50,  2.0,   1.0,
                        step=0.05,
                        on_cc=_on_mecha_event, on_dc=_on_mecha_live)

    mc.separator(h=6)
    sym_cb    = mc.checkBox(label='Simetría',        value=True,
                            changeCommand=_on_mecha_event)
    panels_cb = mc.checkBox(label='Emplear Paneles', value=True,
                            changeCommand=_on_mecha_event)

    mc.separator(h=8)
    mc.text(label='Semilla  (dejar vacío = aleatoria)',
            align='left', font='smallPlainLabelFont')
    seed_field = mc.textField(placeholderText='— semilla generada —',
                              editable=True, width=310)

    mc.separator(h=10)

    # Botones manuales
    m_btn_row = mc.rowLayout(nc=3, cw3=[100, 100, 100],
                             columnAttach3=['both','both','both'],
                             columnOffset3=[0,4,4])

    def _collect_mecha_params():
        return {
            'separation':      mc.floatSliderGrp(sep_sl,   q=True, value=True),
            'connector_angle': mc.floatSliderGrp(angle_sl, q=True, value=True),
            'aggressiveness':  mc.floatSliderGrp(aggr_sl,  q=True, value=True),
            'decay':           mc.floatSliderGrp(decay_sl, q=True, value=True),
            'height_scale':    mc.floatSliderGrp(height_sl,q=True, value=True),
            'symmetry':        mc.checkBox(sym_cb,   q=True, value=True),
            'use_panels':      mc.checkBox(panels_cb,q=True, value=True),
        }

    def _resolve_seed() -> int:
        txt = mc.textField(seed_field, q=True, text=True).strip()
        if txt.isdigit():
            return int(txt)
        s = random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(s))
        return s

    def _rebuild_mecha(*_):
        """Reconstruye solo el mecha, conserva el terreno existente."""
        seed = _SEED[0] or _resolve_seed()
        _SEED[0] = seed
        params = _collect_mecha_params()
        params['_seed'] = seed

        # Eliminar mecha anterior
        for pat in ['RetroMecha_*']:
            for n in (mc.ls(pat, type='transform') or []):
                try: mc.delete(n)
                except: pass

        from core.mecha_builder import MechaBuilder
        grp = MechaBuilder(params, seed=seed).build()
        if grp and mc.objExists(grp):
            _MECHA_GRP[0] = grp
            # Elevar mecha sobre el suelo (mismo offset que SceneComposer)
            try:
                bb   = mc.exactWorldBoundingBox(grp)
                lift = 0.5 - bb[1]
                if abs(lift) > 0.01:
                    mc.move(0, lift, 0, grp, relative=True, worldSpace=True)
            except Exception:
                pass
            mc.select(grp)
            mc.viewFit()

    def _on_gen_mecha(*_):
        """Botón manual: genera semilla nueva + mecha."""
        _SEED[0] = _resolve_seed()
        _rebuild_mecha()

    def _on_random_mecha(*_):
        """Aleatoriza todos los sliders del mecha y reconstruye."""
        import random as rnd
        mc.floatSliderGrp(sep_sl,   e=True, value=rnd.uniform(0.10, 0.80))
        mc.floatSliderGrp(angle_sl, e=True, value=rnd.uniform(0.0,  45.0))
        mc.floatSliderGrp(aggr_sl,  e=True, value=rnd.uniform(0.0,   1.0))
        mc.floatSliderGrp(decay_sl, e=True, value=rnd.uniform(0.50,  1.0))
        mc.floatSliderGrp(height_sl,e=True, value=rnd.uniform(0.50,  2.0))
        mc.checkBox(sym_cb,   e=True, value=rnd.choice([True, False]))
        _SEED[0] = random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(_SEED[0]))
        _rebuild_mecha()

    def _on_reset(*_):
        patterns = ['RetroMecha_*'] + TERRAIN_PATTERNS
        for pat in patterns:
            for n in (mc.ls(pat, type='transform') or []):
                try: mc.delete(n)
                except: pass
        mc.textField(seed_field, e=True, text='')
        _SEED[0]      = None
        _MECHA_GRP[0] = None
        print('[RetroMecha] Escena limpiada')

    mc.button(label='Generar',  h=36, bgc=[0.18, 0.42, 0.22],
              command=_on_gen_mecha)
    mc.button(label='🎲 Mutar', h=36, bgc=[0.42, 0.18, 0.38],
              command=_on_random_mecha)
    mc.button(label='Resetear', h=36, bgc=[0.38, 0.18, 0.18],
              command=_on_reset)
    mc.setParent('..')   # salir btn_row
    mc.separator(h=6, style='none')
    mc.setParent(tabs)

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 2 — TERRENO
    # ──────────────────────────────────────────────────────────────────────────
    terrain_col = mc.columnLayout(adjustableColumn=True,
                                  rowSpacing=4, parent=tabs)
    mc.separator(h=6, style='none')

    # Live checkboxes del terreno
    mc.text(label='Reconstrucción automática', align='left',
            font='smallPlainLabelFont')
    t_row_live = mc.rowLayout(nc=2, cw2=[155, 155])
    t_auto_cb  = mc.checkBox(label='Auto (al soltar)', value=True)
    t_live_cb  = mc.checkBox(label='Live (arrastrar)', value=False)
    mc.setParent('..')
    mc.separator(h=6)

    # Callbacks terreno
    def _on_terrain_event(*_):
        if mc.checkBox(t_auto_cb, q=True, v=True):
            _rebuild_terrain()

    def _on_terrain_live(*_):
        if mc.checkBox(t_live_cb, q=True, v=True):
            _rebuild_terrain()

    # Sliders de terreno
    def tslider(label, mn, mx, val, step=0.01, prec=2):
        mc.text(label=label, align='left', font='smallPlainLabelFont')
        return mc.floatSliderGrp(
            min=mn, max=mx, value=val, step=step, field=True,
            precision=prec,
            columnWidth3=[130, 52, 110],
            columnAlign3=['left','left','left'],
            changeCommand=_on_terrain_event,
            dragCommand=_on_terrain_live,
        )

    def tislider(label, mn, mx, val):
        """Slider entero para conteos."""
        mc.text(label=label, align='left', font='smallPlainLabelFont')
        return mc.intSliderGrp(
            min=mn, max=mx, value=val, field=True,
            columnWidth3=[130, 52, 110],
            columnAlign3=['left','left','left'],
            changeCommand=_on_terrain_event,
            dragCommand=_on_terrain_live,
        )

    mc.text(label='Preset de escena', align='left',
            font='smallPlainLabelFont')
    preset_menu = mc.optionMenu(width=310,
                                changeCommand=_on_terrain_event)
    mc.menuItem(label='Avanzada')
    mc.menuItem(label='Hangar')
    mc.menuItem(label='Campo de batalla')
    mc.menuItem(label='Centinela')

    mc.separator(h=6)
    t_monument_sl  = tslider('Escala monumento',   3.0, 9.0, 5.5, step=0.1)
    t_platcount_sl = tislider('N° plataformas',    3,   16,  8)
    t_fragcount_sl = tislider('N° fragmentos',     2,   24, 12)
    t_debris_sl    = tislider('Debris (piezas)',  20,  150, 80)
    t_pillar_sl    = tislider('Pilares',           2,   16,  8)
    t_ramp_sl      = tslider('Prob. rampas',       0.0,  1.0, 0.55)
    t_ringmax_sl   = tslider('Radio máx. terreno', 8.0, 35.0, 22.0, step=0.5)

    mc.separator(h=8)

    def _collect_terrain_overrides() -> dict:
        """Lee los sliders del tab Terreno."""
        return {
            'monument_scale':    mc.floatSliderGrp(t_monument_sl, q=True, value=True),
            'platform_count':    mc.intSliderGrp(t_platcount_sl,  q=True, value=True),
            'fragment_count':    mc.intSliderGrp(t_fragcount_sl,  q=True, value=True),
            'debris_count':      mc.intSliderGrp(t_debris_sl,     q=True, value=True),
            'pillar_count':      mc.intSliderGrp(t_pillar_sl,     q=True, value=True),
            'ramp_probability':  mc.floatSliderGrp(t_ramp_sl,     q=True, value=True),
            'ring_max_r':        mc.floatSliderGrp(t_ringmax_sl,  q=True, value=True),
        }

    def _rebuild_terrain(*_):
        """Elimina terreno existente y reconstruye con params actuales."""
        # Limpiar terreno anterior
        for pat in TERRAIN_PATTERNS:
            for n in (mc.ls(pat, type='transform') or []):
                try: mc.delete(n)
                except: pass
        # También limpiar grupos de escena pero conservar mecha
        for n in (mc.ls('RetroMecha_Scene_*', type='transform') or []):
            try: mc.delete(n)
            except: pass

        # Necesita un mecha existente para calcular bbox
        mecha_grp = _MECHA_GRP[0]
        if mecha_grp is None or not mc.objExists(mecha_grp):
            # Intentar encontrar cualquier mecha en escena
            found = mc.ls('RetroMecha_*', type='transform') or []
            mecha_grp = found[0] if found else None

        # Calcular bbox del mecha
        mecha_bbox = (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)  # fallback
        if mecha_grp and mc.objExists(mecha_grp):
            try:
                mecha_bbox = tuple(mc.exactWorldBoundingBox(mecha_grp))
            except Exception:
                pass

        # Recopilar params del mecha (tab 1) + overrides del terreno (tab 2)
        params = _collect_mecha_params()
        seed   = _SEED[0] or 42
        params['_seed'] = seed

        preset_label = mc.optionMenu(preset_menu, q=True, value=True)
        preset_name  = PRESET_MAP.get(preset_label, 'avanzada')

        overrides = _collect_terrain_overrides()

        from terrain.terrain_builder import TerrainBuilder
        tb = TerrainBuilder(
            params=params,
            seed=seed + 1000,
            preset_name=preset_name,
            mecha_bbox=mecha_bbox,
        )
        # Inyectar overrides directamente en el preset cargado
        tb.preset.update(overrides)

        grp = tb.build()
        if grp and mc.objExists(grp):
            mc.select(grp)
            mc.viewFit()

    def _on_gen_scene(*_):
        """Genera escena completa desde cero (mecha + terreno)."""
        _SEED[0] = _resolve_seed()
        params = _collect_mecha_params()
        params['_seed'] = _SEED[0]

        preset_label = mc.optionMenu(preset_menu, q=True, value=True)
        preset_name  = PRESET_MAP.get(preset_label, 'avanzada')
        overrides    = _collect_terrain_overrides()

        # Limpiar escena completa
        _on_reset()

        from terrain.scene_composer import SceneComposer
        sc = SceneComposer(params, seed=_SEED[0],
                           terrain_preset=preset_name)

        # Sobrescribir overrides del preset después de instanciar el builder
        # (SceneComposer crea TerrainBuilder internamente, necesitamos parcharlo)
        import terrain.terrain_builder as tb_mod
        _orig_init = tb_mod.TerrainBuilder.__init__

        def _patched_init(self_tb, *a, **kw):
            _orig_init(self_tb, *a, **kw)
            self_tb.preset.update(overrides)

        tb_mod.TerrainBuilder.__init__ = _patched_init
        try:
            grp = sc.compose()
        finally:
            tb_mod.TerrainBuilder.__init__ = _orig_init   # restaurar siempre

        if grp and mc.objExists(grp):
            # Guardar referencia al mecha interno
            children = mc.listRelatives(grp, children=True,
                                        type='transform') or []
            for ch in children:
                if ch.startswith('RetroMecha_') and 'Scene' not in ch:
                    _MECHA_GRP[0] = ch
                    break
            mc.select(grp)
            mc.viewFit()

    def _on_random_terrain(*_):
        """Aleatoriza los sliders del terreno y reconstruye."""
        import random as rnd
        mc.floatSliderGrp(t_monument_sl, e=True,
                          value=rnd.uniform(3.0, 9.0))
        mc.intSliderGrp(t_platcount_sl, e=True,
                        value=rnd.randint(3, 16))
        mc.intSliderGrp(t_fragcount_sl, e=True,
                        value=rnd.randint(2, 24))
        mc.intSliderGrp(t_debris_sl,    e=True,
                        value=rnd.randint(20, 150))
        mc.intSliderGrp(t_pillar_sl,    e=True,
                        value=rnd.randint(2, 16))
        mc.floatSliderGrp(t_ramp_sl,    e=True,
                          value=rnd.uniform(0.0, 1.0))
        mc.floatSliderGrp(t_ringmax_sl, e=True,
                          value=rnd.uniform(10.0, 35.0))
        _rebuild_terrain()

    # Botones del tab Terreno
    t_btn_row = mc.rowLayout(nc=3, cw3=[100, 100, 100],
                             columnAttach3=['both','both','both'],
                             columnOffset3=[0,4,4])
    mc.button(label='Gen. Escena',   h=36, bgc=[0.18, 0.35, 0.45],
              command=_on_gen_scene)
    mc.button(label='🎲 Mutar',      h=36, bgc=[0.42, 0.18, 0.38],
              command=_on_random_terrain)
    mc.button(label='Solo Terreno',  h=36, bgc=[0.25, 0.25, 0.25],
              command=_rebuild_terrain)
    mc.setParent('..')
    mc.separator(h=6, style='none')

    mc.text(label='Solo Terreno requiere un mecha ya generado en la escena.',
            align='center', font='smallPlainLabelFont')
    mc.separator(h=6, style='none')
    mc.setParent(tabs)

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 3 — MATERIALES
    # ──────────────────────────────────────────────────────────────────────────
    mat_col = mc.columnLayout(adjustableColumn=True,
                              rowSpacing=6, parent=tabs)
    mc.separator(h=14, style='none')
    mc.text(label='Materiales — próxima fase',
            align='center', font='boldLabelFont')
    mc.separator(h=8)
    mc.text(label='Aquí se configurarán:', align='left')
    mc.text(label='  • Shaders retro-futuristas (Lambert / Blinn / PBR)', align='left')
    mc.text(label='  • Paleta por preset: oxidado · pulido · mate',       align='left')
    mc.text(label='  • Asignación automática por módulo (mecha y terreno)',align='left')
    mc.text(label='  • Color base + roughness por agresividad',           align='left')
    mc.separator(h=14, style='none')
    mc.setParent(tabs)

    # ── Asignar labels ────────────────────────────────────────────────────────
    mc.tabLayout(tabs, edit=True, tabLabel=[
        (mecha_col,   'Mecha'),
        (terrain_col, 'Terreno'),
        (mat_col,     'Materiales'),
    ])

    mc.showWindow(win)
    print('[RetroMecha] UI v3 abierta')