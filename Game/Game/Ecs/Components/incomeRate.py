from dataclasses import dataclass

@dataclass
class IncomeRate:
    """
    Component IncomeRate. Définit le taux de production de "coups de fouet".
    
    Attributes:
        rate: Taux de production de base.
        multiplier: Multiplicateur temporaire (événements).
    """
    rate: float = 1.0
    multiplier: float = 1.0

    # permet d'obtenir le taux effectif
    @property
    def effective_rate(self) -> float:
        """Retourne le taux effectif (rate × multiplier)."""
        return self.rate * self.multiplier

    # permet de modifier le taux effectif
    def __post_init__(self):
        if self.rate < 0:
            self.rate = 1.0

    # Permet d'afficher le composant de manière lisible
    def __str__(self):
        return f"IncomeRate(rate={self.rate}, mult={self.multiplier})"

    # Permet d'afficher le composant de maniern lisible avec repr au lieu de str 
    def __repr__(self):
        return self.__str__()

    # Permet d'afficher le composant de maniern lisible en dict format
    def to_dict(self):
        return {"rate": self.rate, "multiplier": self.multiplier}
