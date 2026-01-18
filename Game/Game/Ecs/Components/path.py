from dataclasses import dataclass
from typing import List
from .grid_position import GridPosition


@dataclass
class Path:
    """Composant ECS décrivant le chemin à suivre pour une entité.

    Attributes:
        noeuds: Liste ordonnée des positions (GridPosition) que l’entité doit suivre
                pour atteindre sa destination.
    """
    noeuds: List[GridPosition]
