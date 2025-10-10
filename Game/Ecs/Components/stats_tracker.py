from dataclasses import dataclass

@dataclass
class StatsTracker:
    """
    Statistiques de partie (utilisé pour l'écran de fin, HUD, etc.).

    Args:
        unites_achetees: nombre total d'unités achetées.
        degats_total: dégâts infligés cumulés.
        niv_pyramide: niveau actuel de la pyramide (min 0 / max 5 dans le GDD).
    """
    unites_achetees: int = 0
    degats_total: float = 0.0
    niv_pyramide: int = 0

    # Petites aides d'update
    def add_unit(self, n: int = 1) -> None:
        if n > 0:
            self.unites_achetees += n

    def add_damage(self, amount: float) -> None:
        if amount > 0.0:
            self.degats_total += amount

    def set_pyramid_level(self, level: int) -> None:
        if level >= 0:
            self.niv_pyramide = level

    def to_dict(self):
        return {
            "unites_achetees": int(self.unites_achetees),
            "degats_total": float(self.degats_total),
            "niv_pyramide": int(self.niv_pyramide),
        }
