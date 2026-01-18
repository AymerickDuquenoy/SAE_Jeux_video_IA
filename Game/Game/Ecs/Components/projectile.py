from dataclasses import dataclass

@dataclass
class Projectile:
    """
    Projectile simple :
    - team_id : équipe qui a tiré
    - target_entity_id : cible visée au moment du tir
    - damage : dégâts à appliquer à l'impact
    - hit_radius : distance (en unités grille) pour considérer que ça touche
    """
    team_id: int
    target_entity_id: int
    damage: float = 5.0
    hit_radius: float = 0.18
