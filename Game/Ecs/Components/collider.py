from dataclasses import dataclass
from typing import Tuple

@dataclass
class Collider:
    """
    Component Collider. Définit une forme de collision simple pour les entités.
    
    Attributes:
        size: Taille (width, height) pour les boîtes (Tuple[float, float]).
    """
    size: Tuple[float, float] = None

    def __post_init__(self):
        # S'assurer que size est défini pour les box
        if self.size is None:
            raise ValueError("Collider de type 'box' doit avoir une size (width, height).")
        
    
