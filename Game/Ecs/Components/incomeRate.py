from dataclasses import dataclass

@dataclass
class IncomeRate:
    """
    Component IncomeRate. Définit le taux de production de "coups de fouet".
    
    Attributes:
        rate: Taux de production.
    """
    rate: float = 1.0

    # S'assurer que le rate est positif (le mettre à 1 sinon)
    def __post_init__(self):
        if self.rate < 0:
            self.rate = 1.0

    def __str__(self):
        return f"IncomeRate(rate={self.rate})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"rate": self.rate}
