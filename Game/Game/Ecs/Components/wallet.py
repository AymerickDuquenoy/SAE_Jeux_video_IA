from dataclasses import dataclass

@dataclass
# Composant qui stocke le solde de 'coups de fouet' (monnaie du jeu)
class Wallet:
    """
    Component Wallet. Définit le solde de "coups de fouet" du joueur.
    
    Attributes:
        solde: Solde du wallet.
    """
    solde: float = 0.0

    # S'assurer que le solde n'est pas négatif (le mettre à zéro sinon)
    # Validation : s'assure que le solde n'est jamais négatif
    def __post_init__(self):
        if self.solde < 0:
            self.solde = 0.0

    # Retourne une représentation textuelle du wallet
    def __str__(self):
        return f"Wallet(solde={self.solde})"

    # Retourne une représentation pour le débogage
    def __repr__(self):
        return self.__str__()

    # Convertit le wallet en dictionnaire pour sérialisation
    def to_dict(self):
        return {"solde": self.solde}