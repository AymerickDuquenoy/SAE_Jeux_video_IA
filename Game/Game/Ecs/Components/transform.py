from dataclasses import dataclass
from typing import Tuple

# Alias de type pour un vecteur 2D (x, y).
Vec2 = Tuple[float, float]

@dataclass
# Composant qui définit la position, rotation et échelle d'une entité dans le monde 2D
class Transform:
    """Composant ECS décrivant la pose 2D d'une entité en coordonnées monde.

    Attributes:
        pos: Position monde (x, y).
        rot: Rotation en radians (sens anti-horaire).
        scale: Échelle (sx, sy). Utiliser (-1, 1) pour un flip horizontal.
    """
    pos: Vec2 = (0.0, 0.0)
    rot: float = 0.0
    scale: Vec2 = (1.0, 1.0)