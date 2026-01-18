from dataclasses import dataclass

@dataclass
class AttackCooldown:
    """
    Gère un cooldown d'attaque simple.
    - cooldown : temps entre deux coups (s)
    - timer : temps restant avant prochain coup (s)
    """
    cooldown: float = 0.7
    timer: float = 0.0
