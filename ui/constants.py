"""Shared UI labels and value maps for RetroMecha."""

HEAD_STYLE_LABELS = {
    'Casco': 'helmet', 'Dron': 'drone', 'Centinela': 'sentinel',
    'Cráneo': 'skull', 'Kabuto': 'kabuto',
}
ARM_STYLE_LABELS = {
    'Estándar': 'standard', 'Pesado': 'heavy',
    'Cuchilla': 'blade', 'Cañón': 'cannon',
    'Escudo': 'shield',
}
WING_STYLE_LABELS = {
    'Agujas': 'needle', 'Compactas': 'compact', 'Abanico': 'fan',
    'Delta': 'delta',
    'Mantle': 'mantle',
}
TORSO_STYLE_LABELS = {
    'Base': 'core', 'Pesado': 'heavy', 'Delgado': 'slim', 'Compacto': 'compact',
    'Samurái': 'samurai', 'Insecto': 'insect',
}
NUCLEUS_STYLE_LABELS = {
    'Anillo': 'ring', 'Columna': 'column', 'Orbe': 'orb',
    'Cruz': 'cross', 'Orbes': 'orb_cluster',
}
TERRAIN_PRESET_MAP = {
    'Avanzada': 'avanzada', 'Hangar': 'hangar',
    'Campo de batalla': 'campo_de_batalla', 'Centinela': 'centinela',
}

STYLE_MAPS = {
    'head': HEAD_STYLE_LABELS,
    'arm': ARM_STYLE_LABELS,
    'wing': WING_STYLE_LABELS,
    'torso': TORSO_STYLE_LABELS,
    'nucleus': NUCLEUS_STYLE_LABELS,
}

# Colores representativos para swatches de paleta (modo Rápido y Pro)
PALETTE_SWATCH_COLORS = {
    'Industrial': ([0.55, 0.54, 0.51], 'Predeterminado'),
    'Oxidado': ([0.55, 0.30, 0.15], 'Oxidado'),
    'Frio': ([0.30, 0.55, 0.75], 'Frio'),
    'Atardecer': ([0.65, 0.22, 0.35], 'Atardecer'),
    'Neon': ([0.85, 0.20, 0.85], 'Neon'),
    'Magma': ([0.95, 0.30, 0.05], 'Magma'),
    'Veneno': ([0.10, 0.90, 0.25], 'Veneno'),
}
