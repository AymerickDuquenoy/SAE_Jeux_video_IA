from dataclasses import dataclass

@dataclass
class Speed:
    """Composant ECS décrivant la vitesse nominale d'une entité.

    Attributes:
        base: Vitesse de base en unités monde par seconde.
        mult_terrain: Multiplicateur (ex. 1.0 sable, 0.5 sables mouvants).
    """
    base: float = 2.5
    mult_terrain: float = 1.0
