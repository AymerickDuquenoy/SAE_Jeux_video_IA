from typing import List, Optional


class NavigationGrid:
    """
    Grille de navigation pour A*.

    Chaque case a :
      - walkable : traversable ou non
      - mult : multiplicateur de vitesse (1.0 normal, 0.5 lent, 0 bloqué)

    A* utilise :
      - is_walkable(x,y)
      - movement_cost(x,y)
    """

    # Initialise une grille de navigation avec dimensions et valeurs par défaut
    def __init__(self, width: int, height: int, default_walkable: bool = True, default_mult: float = 1.0):
        self.width = int(width)
        self.height = int(height)

        self.walkable: List[List[bool]] = [
            [bool(default_walkable) for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.mult: List[List[float]] = [
            [float(default_mult) for _ in range(self.width)]
            for _ in range(self.height)
        ]

    # Vérifie si une position est dans les limites de la grille
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    # Définit la traversabilité et le multiplicateur d'une case
    def set_cell(self, x: int, y: int, *, walkable: Optional[bool] = None, mult: Optional[float] = None):
        if not self.in_bounds(x, y):
            return
        if walkable is not None:
            self.walkable[y][x] = bool(walkable)
        if mult is not None:
            self.mult[y][x] = float(mult)

    # Retourne si une case est traversable
    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return self.walkable[y][x]

    # Retourne le coût de déplacement pour entrer dans une case
    def movement_cost(self, x: int, y: int) -> float:
        """
        Coût pour entrer dans (x,y) :
        - mult <= 0 => inf (case bloquée)
        - sinon coût = 1 / mult (case lente => + cher)
        """
        if not self.in_bounds(x, y):
            return float("inf")
        m = float(self.mult[y][x])
        if m <= 0:
            return float("inf")
        return 1.0 / m