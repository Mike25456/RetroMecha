"""
RetroMecha — core/base_module.py  v2 + materials
Clase base con pipeline generativo completo:

  generate()
    ├─ _build_X()           ← geometría manual del módulo
    ├─ _deform_mesh()       ← escala no-uniforme + vertex displacement
    ├─ _attach_subpieces()  ← snap/conform sobre la superficie
    ├─ _assign_materials()  ← aiToon por tier (ARMOR/JOINT/DETAIL/GLOW)
    ├─ _cleanup_history()   ← deleteHistory final
    └─ _finalize_group()    ← posiciona en mundo

COMPATIBILIDAD TOTAL con módulos existentes (head/torso/arm/wing):
  Solo necesitan llamar opcionalmente:
    self._deform_mesh(main_mesh)
    self._attach_subpieces(grp, main_mesh)
    self._assign_materials(grp)         ← NUEVO
    self._cleanup_history(grp)
    return self._finalize_group(grp, position, rotation, scale)
"""

import json
import os
import random
from abc import ABC, abstractmethod

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


class BaseModule(ABC):

    MODULE_NAME: str = ""

    def __init__(self, params: dict = None):
        self.params = params or {}
        _seed = self.params.get('_seed', 42)
        self._rng = random.Random(_seed + hash(self.MODULE_NAME) % 10000)

    @abstractmethod
    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:
        """Crea la geometría del módulo. Retorna nombre del grupo raíz."""
        pass

    # ══════════════════════════════════════════════════════════════════════════
    #  DEFORMACIÓN
    # ══════════════════════════════════════════════════════════════════════════

    def _deform_mesh(self, mesh: str):
        if not MAYA_AVAILABLE or not mesh or not mc.objExists(mesh):
            return
        try:
            from utils.deform_utils import deform_pipeline
            aggr = self._get('aggressiveness', 0.5)
            h_sc = self._get('height_scale', 1.0)
            deform_pipeline(mesh, aggr, h_sc, self._rng)
        except ImportError:
            pass
        except Exception as e:
            print(f'[RetroMecha][BaseModule] _deform_mesh: {e}')

    # ══════════════════════════════════════════════════════════════════════════
    #  SUB-PIEZAS
    # ══════════════════════════════════════════════════════════════════════════

    def _attach_subpieces(self, grp: str, target_mesh: str):
        if not MAYA_AVAILABLE:
            return
        subpieces = self._load_subpieces()
        if not subpieces:
            return
        aggr = self._get('aggressiveness', 0.5)
        for sp_name, sp_cfg in subpieces.items():
            base_prob = sp_cfg.get('probability', 0.5)
            prob = (base_prob * (0.4 + aggr * 0.6)
                    if sp_cfg.get('type') == 'snap' else base_prob)
            if self._rng.random() > prob:
                continue
            try:
                self._create_and_attach(sp_name, sp_cfg, grp, target_mesh)
            except Exception as e:
                print(f'[RetroMecha][BaseModule] sub-pieza {sp_name}: {e}')

    def _create_and_attach(self, name, cfg, grp, target_mesh):
        attach_type = cfg.get('type', 'snap')
        geom_cfg    = cfg.get('geometry', {})
        scale_range = cfg.get('scale_range', [0.8, 1.2])
        hint        = cfg.get('position_hint', 'front')
        sp_scale    = self._rng.uniform(*scale_range)
        desired_pos = self._hint_to_pos(target_mesh, hint)

        if attach_type == 'snap':
            piece = self._make_geom(name, geom_cfg, sp_scale)
            if piece:
                self._snap_to_mesh(piece, target_mesh, desired_pos)
                mc.parent(piece, grp)
        elif attach_type == 'conform':
            piece = self._make_geom(name, geom_cfg, sp_scale)
            if piece:
                mc.move(*desired_pos, piece, worldSpace=True)
                self._conform_to_mesh(piece, target_mesh,
                                      offset=cfg.get('offset', 0.03))
                mc.parent(piece, grp)
        elif attach_type == 'conform_stack':
            count   = cfg.get('count', 3)
            offsets = cfg.get('offsets', [0.03, 0.06, 0.09])
            panels  = []
            for i in range(count):
                p = self._make_geom(f'{name}_{i}', geom_cfg,
                                    sp_scale * (1.0 - i * 0.15))
                if p:
                    mc.move(*desired_pos, p, worldSpace=True)
                    panels.append(p)
            if panels:
                self._conform_stack(panels, target_mesh, offsets[:len(panels)])
                for p in panels:
                    mc.parent(p, grp)

    def _snap_to_mesh(self, piece, target_mesh, desired_pos, offset=0.02):
        if not MAYA_AVAILABLE: return
        try:
            from utils.surface_utils import snap_to_mesh
            snap_to_mesh(piece, target_mesh, desired_pos, offset=offset)
        except ImportError:
            try: mc.move(*desired_pos, piece, worldSpace=True)
            except: pass

    def _conform_to_mesh(self, panel, target_mesh, offset=0.03):
        if not MAYA_AVAILABLE: return
        try:
            from utils.surface_utils import conform_to_mesh
            conform_to_mesh(panel, target_mesh, offset=offset)
        except ImportError:
            pass

    def _conform_stack(self, panels, target_mesh, offsets=None):
        if not MAYA_AVAILABLE: return
        try:
            from utils.surface_utils import conform_stack
            conform_stack(panels, target_mesh, offsets)
        except ImportError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  MATERIALES (NUEVO)
    # ══════════════════════════════════════════════════════════════════════════

    def _assign_materials(self, grp: str):
        """
        Asigna materiales aiToon a cada pieza del grupo según su tier.
        Lee el parámetro 'palette' del módulo (default: 'industrial').
        Si la UI no envía 'palette', usa el default.
        """
        if not MAYA_AVAILABLE:
            return
        try:
            from utils.material_assigner import assign_palette_to_group
            palette = self._get('palette', 'industrial')
            assign_palette_to_group(grp, palette)
        except ImportError:
            pass  # material_assigner no disponible — los módulos siguen
                  # usando assign_material() de maya_materials.py directamente
        except Exception as e:
            print(f'[RetroMecha][BaseModule] _assign_materials: {e}')

    # ══════════════════════════════════════════════════════════════════════════
    #  LIMPIEZA
    # ══════════════════════════════════════════════════════════════════════════

    def _cleanup_history(self, grp: str):
        if not MAYA_AVAILABLE:
            return
        try:
            descendants = mc.listRelatives(
                grp, allDescendents=True, type='transform') or []
            for n in descendants:
                try: mc.delete(n, constructionHistory=True)
                except: pass
            try: mc.delete(grp, constructionHistory=True)
            except: pass
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  HELPERS PRIVADOS DE SUB-PIEZAS
    # ══════════════════════════════════════════════════════════════════════════

    def _make_geom(self, name, geom_cfg, scale):
        prefix = f'rm_sp_{self.MODULE_NAME.lower()}_{name}_#'
        shape = geom_cfg.get('shape', 'cube')
        try:
            if shape == 'cube':
                return mc.polyCube(w=geom_cfg.get('w', 0.3)*scale,
                                   h=geom_cfg.get('h', 0.2)*scale,
                                   d=geom_cfg.get('d', 0.03)*scale,
                                   name=prefix)[0]
            elif shape == 'cone':
                return mc.polyCone(r=geom_cfg.get('r', 0.08)*scale,
                                   h=geom_cfg.get('h', 0.25)*scale,
                                   sa=geom_cfg.get('sa', 4),
                                   name=prefix)[0]
            elif shape == 'cylinder':
                return mc.polyCylinder(r=geom_cfg.get('r', 0.07)*scale,
                                       h=geom_cfg.get('h', 0.3)*scale,
                                       sa=geom_cfg.get('sa', 6),
                                       name=prefix)[0]
            elif shape == 'sphere':
                return mc.polySphere(r=geom_cfg.get('r', 0.06)*scale,
                                     sa=geom_cfg.get('sa', 6),
                                     sh=geom_cfg.get('sh', 4),
                                     name=prefix)[0]
            elif shape == 'torus':
                return mc.polyTorus(r=geom_cfg.get('r', 0.15)*scale,
                                    sr=geom_cfg.get('sr', 0.03)*scale,
                                    sa=geom_cfg.get('sa', 8),
                                    sh=geom_cfg.get('sh', 4),
                                    name=prefix)[0]
            return mc.polyCube(w=0.2*scale, h=0.2*scale, d=0.2*scale,
                               name=prefix)[0]
        except Exception as e:
            print(f'[RetroMecha][BaseModule] _make_geom {name}: {e}')
            return None

    def _hint_to_pos(self, mesh, hint):
        try:
            bb = mc.exactWorldBoundingBox(mesh)
            cx = (bb[0]+bb[3])*0.5
            cy = (bb[1]+bb[4])*0.5
            cz = (bb[2]+bb[5])*0.5
            jx = self._rng.uniform(-0.15, 0.15) * (bb[3]-bb[0])
            jz = self._rng.uniform(-0.15, 0.15) * (bb[5]-bb[2])
            if hint == 'top':     return (cx+jx, bb[4], cz+jz)
            if hint == 'front':   return (cx+jx, cy, bb[5])
            if hint == 'back':    return (cx+jx, cy, bb[2])
            if hint == 'lateral': return (self._rng.choice([bb[0],bb[3]]), cy, cz+jz)
            if hint == 'bottom':  return (cx+jx, bb[1], cz+jz)
            return (cx+jx, cy, cz+jz)
        except Exception:
            return (0,0,0)

    def _load_subpieces(self) -> dict:
        path = os.path.join(os.path.dirname(__file__),
                            '..', 'config', 'subpieces.json')
        try:
            if os.path.exists(path):
                return json.load(open(path)).get(self.MODULE_NAME, {})
        except Exception:
            pass
        return {}

    # ══════════════════════════════════════════════════════════════════════════
    #  INTERFAZ PÚBLICA HEREDADA
    # ══════════════════════════════════════════════════════════════════════════

    def _finalize_group(self, group, position, rotation, scale):
        if not MAYA_AVAILABLE:
            return group
        mc.move(*position, group)
        mc.rotate(*rotation, group)
        mc.scale(scale, scale, scale, group)
        return group

    def _get(self, key: str, default=None):
        return self.params.get(key, default)
