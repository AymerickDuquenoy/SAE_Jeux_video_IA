from dataclasses import dataclass

@dataclass
class Damage:
    """Composant ECS décrivant une valeur de dégâts brute.

    Attributes:
        value: Dégâts infligés (peuvent être décimaux avant arrondi système).
    """
    value: float = 10.0
