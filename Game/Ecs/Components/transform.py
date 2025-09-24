from dataclasses import dataclass
from typing import Tuple

# Alias de type : vecteur 2D (x, y)
Vec2 = Tuple[float, float]

@dataclass
class Transform:
    """Transformation 2D : position monde (x, y), rotation (radians), échelle (sx, sy)."""
    pos: Vec2 = (0.0, 0.0)     # Position en coordonnées monde
    rot: float = 0.0           # Angle en radians (sens anti-horaire)
    scale: Vec2 = (1.0, 1.0)   # Échelle (sx, sy) ; (-1, 1) = flip horizontal
