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
# Composant qui applique les effets du terrain sur la vitesse des unités
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

    # Initialise le facteur de ralentissement selon le type de terrain
    def __post_init__(self):
        if self.slow_factor is None:
            self.slow_factor = TERRAIN_SLOW_BY_TYPE.get(self.type, 1.0)
        # Garde-fous simples
        if self.slow_factor < 0.0:
            self.slow_factor = 0.0

    # Applique le facteur de ralentissement à une vitesse de base
    def apply(self, base_speed: float) -> float:
        """Retourne base_speed * slow_factor (≥ 0)."""
        return max(0.0, base_speed * float(self.slow_factor))

    # Convertit le composant en dictionnaire pour sérialisation
    def to_dict(self):
        return {"type": self.type, "slow_factor": float(self.slow_factor)}