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

    @property
    def effective_rate(self) -> float:
        """Retourne le taux effectif (rate × multiplier)."""
        return self.rate * self.multiplier

    def __post_init__(self):
        if self.rate < 0:
            self.rate = 1.0

    def __str__(self):
        return f"IncomeRate(rate={self.rate}, mult={self.multiplier})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"rate": self.rate, "multiplier": self.multiplier}
