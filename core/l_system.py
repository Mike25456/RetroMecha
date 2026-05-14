"""
RetroMecha — core/l_system.py
Motor del sistema L: expansión de cadenas y parseo a instrucciones de build.

Las reglas base vienen del documento técnico del proyecto.
Se pueden sobrescribir cargando config/l_system_rules.json.
"""

import random
import json
import os

# ── Reglas base (del documento técnico) ─────────────────────────────────────
DEFAULT_RULES = {
    # Axioma: T (cabeza/head)
    # Iteración 1: genera estructura primaria
    'T': [
        ('T [A J S A] [N J] [W] [W]', 1.0)
    ],
    # Iteración 2: ramificación de segmentos secundarios
    'A': [
        ('A [J] [P C] S', 0.7),
        ('A [J] S',        0.3),
    ],
    # Iteración 3: variación de alas
    'W': [
        ('W [S]',   0.6),
        ('W [S S]', 0.4),
    ],
    # Terminales (no se expanden)
    'J': [('J', 1.0)],
    'N': [('N', 1.0)],
    'P': [('P', 1.0)],
    'C': [('C', 1.0)],
    'S': [('S', 1.0)],
}

# Mapa de símbolo → clave de módulo en el Registry
SYMBOL_TO_MODULE = {
    'T': 'HEAD',
    'N': 'TORSO',
    'A': 'ARM',
    'W': 'WING',
    'P': 'PANEL',
    'C': 'CONNECTOR',
    'J': 'JOINT',
}


class LSystem:
    """
    Motor L-System estocástico para RetroMecha.

    Expande un axioma usando reglas de reescritura con probabilidades
    y produce una lista de instrucciones para el MechaBuilder.
    """

    def __init__(self, seed: int = None, rules: dict = None):
        self.seed = seed
        self._rng = random.Random(seed)
        self.rules = rules or self._load_rules()

    def _load_rules(self) -> dict:
        """Intenta cargar reglas desde JSON; usa defaults si no existe."""
        rules_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'l_system_rules.json'
        )
        if os.path.exists(rules_path):
            try:
                with open(rules_path, 'r') as f:
                    data = json.load(f)
                print('[RetroMecha][LSystem] Reglas cargadas desde JSON')
                return data
            except Exception as e:
                print(f'[RetroMecha][LSystem] Error al cargar reglas JSON: {e}')
        return DEFAULT_RULES

    def expand(self, axiom: str = 'T', iterations: int = 2) -> str:
        """
        Expande el axioma `iterations` veces usando las reglas.

        Args:
            axiom:      símbolo inicial (default 'T' = cabeza)
            iterations: profundidad de expansión (1-3 recomendado)

        Returns:
            Cadena expandida del L-System
        """
        string = axiom
        for i in range(iterations):
            new_string = ''
            for token in string.split():
                token_clean = token.strip('[]')
                if token_clean in self.rules:
                    options = self.rules[token_clean]
                    symbols = [r[0] for r in options]
                    weights = [r[1] for r in options]
                    chosen = self._rng.choices(symbols, weights=weights)[0]
                    # Mantener brackets originales
                    if token.startswith('[') and token.endswith(']'):
                        chosen = f'[{chosen}]'
                    new_string += chosen + ' '
                else:
                    new_string += token + ' '
            string = new_string.strip()
        return string

    def to_build_plan(self, string: str) -> list:
        """
        Convierte una cadena L-System en un plan de construcción.

        Returns:
            Lista de dicts: [{'module': 'HEAD', 'branch': False}, ...]
        """
        plan = []
        tokens = string.split()
        branch_depth = 0

        for token in tokens:
            is_branch = token.startswith('[')
            clean = token.strip('[]')

            if clean in SYMBOL_TO_MODULE:
                plan.append({
                    'module': SYMBOL_TO_MODULE[clean],
                    'branch': branch_depth > 0,
                    'depth': branch_depth,
                })

            # Contar profundidad de rama
            branch_depth += token.count('[') - token.count(']')
            branch_depth = max(0, branch_depth)

        return plan

    def debug_expand(self, axiom: str = 'T', iterations: int = 2):
        """Imprime la expansión paso a paso (útil en desarrollo)."""
        string = axiom
        print(f'[LSystem] Axioma: {string}')
        for i in range(iterations):
            prev = string
            string = self.expand(string, iterations=1)
            print(f'[LSystem] Iter {i+1}: {string}')
        return string
