from dataclasses import dataclass

@dataclass
class Wallet:
    """
    Component Wallet. Définit le solde de "coups de fouet" du joueur.
    
    Attributes:
        solde: Solde du wallet.
    """
    solde: float = 0.0

    # S'assurer que le solde n'est pas négatif (le mettre à zéro sinon)
    def __post_init__(self):
        if self.solde < 0:
            self.solde = 0.0

    """Retourne une chaîne de caractères représentant l'objet."""
    def __str__(self):
        return f"Wallet(solde={self.solde})"

    """Overloading de repr pour faciliter le debugging"""
    def __repr__(self):
        return self.__str__()

    """Retourne un dictionnaire représentant l'objet."""
    def to_dict(self):
        return {"solde": self.solde}
