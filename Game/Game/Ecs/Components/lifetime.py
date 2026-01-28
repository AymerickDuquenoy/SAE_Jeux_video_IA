from dataclasses import dataclass

@dataclass
class Lifetime:
    """
    Gère la durée de vie d'une entité.

    Args:
        ttl: temps de vie (s). -1.0 = infini (pas de décrément).
        despawn_on_death: si True, on despawn quand Health.is_dead == True.
    """
    ttl: float = -1.0
    despawn_on_death: bool = True

    # Permet de décrémenter le TTL s'il n'est pas infini
    def tick(self, dt: float) -> None:
        """Décrémente le TTL s'il n'est pas infini."""
        if self.ttl < 0.0:
            return
        if dt > 0.0:
            self.ttl = max(0.0, self.ttl - dt)

    # True si la durée de vie est écouleurée
    @property
    def expired(self) -> bool:
        """True si la durée de vie est écoulée."""
        return self.ttl == 0.0 if self.ttl >= 0.0 else False

    # Permet d'afficher le composant de maniern lisible en dict format
    def to_dict(self):
        return {"ttl": float(self.ttl), "despawn_on_death": bool(self.despawn_on_death)}
