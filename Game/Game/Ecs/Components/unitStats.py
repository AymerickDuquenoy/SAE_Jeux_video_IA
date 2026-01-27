from dataclasses import dataclass

@dataclass
class UnitStats:
    """
    Component UnitStats.
    Définit les statistiques d'une unité.
    """
    speed: float = 1.0      # Vitesse de déplacement
    power: float = 10.0     # Puissance d'attaque
    armor: float = 5.0      # Niveau de blindage
    cost: float = 100.0     # Coût de l'unité

    def __str__(self):
        return (f"UnitStats(speed={self.speed}, power={self.power}, "
                f"armor={self.armor}, cost={self.cost})")

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "speed": self.speed,
            "power": self.power,
            "armor": self.armor,
            "cost": self.cost
        }