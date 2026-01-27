from dataclasses import dataclass
from typing import Optional

# Valeurs par défaut issues du Game Design :
# - désert : vitesse normale
# - sables mouvants : vitesse divisée par 2
# - pyramide : non traversable (ici = 0.0)
TERRAIN_SLOW_BY_TYPE = {
    "desert": 1.0,
    "quicksand": 0.5,   # sables mouvants
    "pyramid": 0.0,
}

@dataclass
class TerrainEffect:
    """
    Composant TerrainEffect : impact du terrain sur la vitesse.

    Args:
        type: nom du terrain ('desert' | 'quicksand' | 'pyramid' | custom).
        slow_factor: multiplicateur vitesse (si None, déduit de 'type').
                     0.0 = bloqué ; 1.0 = neutre ; >1.0 = accéléré.
    """
    type: str = "desert"
    slow_factor: Optional[float] = None

    """Initialisation post-construction pour définir slow_factor si None."""
    def __post_init__(self):
        if self.slow_factor is None:
            self.slow_factor = TERRAIN_SLOW_BY_TYPE.get(self.type, 1.0)
        # Garde-fous simples
        if self.slow_factor < 0.0:
            self.slow_factor = 0.0

    """Retourne base_speed * slow_factor (≥ 0)."""
    def apply(self, base_speed: float) -> float:
        """Retourne base_speed * slow_factor (≥ 0)."""
        return max(0.0, base_speed * float(self.slow_factor))

    """Retourne un dictionnaire représentant l'objet."""
    def to_dict(self):
        return {"type": self.type, "slow_factor": float(self.slow_factor)}
