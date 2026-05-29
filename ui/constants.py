"""Shared UI labels and value maps for RetroMecha."""

HEAD_STYLE_LABELS = {
    'Casco': 'helmet', 'Drone': 'drone', 'Centinela': 'sentinel',
}
ARM_STYLE_LABELS = {
    'Estandar': 'standard', 'Pesado': 'heavy',
    'Cuchilla': 'blade', 'Cañon': 'cannon',
}
WING_STYLE_LABELS = {
    'Agujas': 'needle', 'Compactas': 'compact', 'Abanico': 'fan',
}
TORSO_STYLE_LABELS = {
    'Base': 'core', 'Pesado': 'heavy', 'Delgado': 'slim', 'Compacto': 'compact',
}
NUCLEUS_STYLE_LABELS = {
    'Anillo': 'ring', 'Columna': 'column', 'Orbe': 'orb',
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
