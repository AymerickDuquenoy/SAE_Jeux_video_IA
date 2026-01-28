from dataclasses import dataclass

@dataclass
# Composant qui stocke les statistiques d'une unité (vitesse, puissance, armure, coût)
class UnitStats:
    """
    Component UnitStats.
    Définit les statistiques d'une unité.
    """
    speed: float = 1.0      # Vitesse de déplacement
    power: float = 10.0     # Puissance d'attaque
    armor: float = 5.0      # Niveau de blindage
    cost: float = 100.0     # Coût de l'unité

    # Retourne une représentation textuelle lisible des statistiques
    def __str__(self):
        return (f"UnitStats(speed={self.speed}, power={self.power}, "
                f"armor={self.armor}, cost={self.cost})")

    # Retourne une représentation pour le débogage
    def __repr__(self):
        return self.__str__()

    # Convertit les statistiques en dictionnaire pour sérialisation
    def to_dict(self):
        return {
            "speed": self.speed,
            "power": self.power,
            "armor": self.armor,
            "cost": self.cost
        }