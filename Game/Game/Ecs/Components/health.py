from dataclasses import dataclass, field

@dataclass
class Health:
    """Composant ECS décrivant la santé d'une entité.

    Attributes:
        hp: Points de vie actuels (>= 0).
        hp_max: Points de vie maximum (>= 1).
    """
    hp_max: int = 100
    hp: int = field(default=100)

    # Méthodes permettant de s'assurer de l'intégrité des données
    def __post_init__(self):
        if self.hp_max < 1:
            self.hp_max = 1
        self.hp = max(0, min(self.hp, self.hp_max))

    # Fonctions permettant de manipuler la santé de l'entité
    @property
    def is_dead(self) -> bool:
        """True si l'entité n'a plus de points de vie."""
        return self.hp <= 0
