from dataclasses import dataclass
from grid_position import GridPosition

@dataclass
class PathRequest:
    """Composant ECS servant à demander le calcul d’un chemin.

    Attributes:
        goal: Position cible (GridPosition) vers laquelle l’entité souhaite aller.
    """
    goal: GridPosition
