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

    """Initialisation post-construction pour garantir les contraintes sur hp et hp_max."""
    def __post_init__(self):
        if self.hp_max < 1:
            self.hp_max = 1
        self.hp = max(0, min(self.hp, self.hp_max))

    @property
    def is_dead(self) -> bool:
        """True si l'entité n'a plus de points de vie."""
        return self.hp <= 0
