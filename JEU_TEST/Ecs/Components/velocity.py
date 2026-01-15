from dataclasses import dataclass

@dataclass
class Velocity:
    """Composant ECS décrivant la vitesse 2D en unités monde par seconde.

    Attributes:
        vx: Composante X de la vitesse (unités/s).
        vy: Composante Y de la vitesse (unités/s).
    """
    vx: float = 0.0
    vy: float = 0.0
