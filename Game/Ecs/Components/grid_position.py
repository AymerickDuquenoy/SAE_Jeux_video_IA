from dataclasses import dataclass

@dataclass
class GridPosition:
    """Composant ECS décrivant la position d'une entité sur la grille.

    Attributes:
        x: Colonne (entier).
        y: Ligne (entier).
    """
    x: int = 0
    y: int = 0
