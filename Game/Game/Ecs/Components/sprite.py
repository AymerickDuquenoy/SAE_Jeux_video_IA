from dataclasses import dataclass

@dataclass
class Sprite:
    """
    Component Sprite. Définit une représentation visuelle pour les entités.
    
    Attributes:
        ref_modele: Référence au modèle/texture (str).
        z: Ordre de rendu (int, plus grand est dessiné au-dessus).
    """
    ref_modele: str = None 
    z: int = 0

    def __post_init__(self):
        # S'assurer que ref_modele est défini
        if self.ref_modele is None:
            raise ValueError("Sprite doit avoir une ref_modele définie.")

    def __str__(self):
        return f"Sprite(ref_modele='{self.ref_modele}', z={self.z})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"ref_modele": self.ref_modele, "z": self.z}