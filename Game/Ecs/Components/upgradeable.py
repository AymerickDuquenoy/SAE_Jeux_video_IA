from dataclasses import dataclass

@dataclass
class Upgradeable:
    """
    Component Upgradeable. Définit un objet upgradeable.
    
    Attributes:
        upgrade_cost: Coût de l'upgrade.
    """
    upgrade_cost: float = 100.0

    def __post_init__(self):
        # S'assurer que upgrade_cost est positif (le mettre à 100 sinon)
        if self.upgrade_cost < 0:
            self.upgrade_cost = 100.0

    def __str__(self):
        return f"Upgradeable(upgrade_cost={self.upgrade_cost})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"upgrade_cost": self.upgrade_cost}
