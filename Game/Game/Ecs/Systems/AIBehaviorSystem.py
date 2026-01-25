"""
AIBehaviorSystem - Comportements IA différenciés par type d'unité.

Selon le Game Design SAÉ:
- Momie (S): Combat sur sa lane
- Dromadaire (M): Combat sur sa lane
- Sphinx (L): Siège - ignore les troupes, cible directement la pyramide

Version optimisée O(n) - pas de flocking.
"""
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target


class AIBehaviorSystem(esper.Processor):
    """
    Comportements IA simplifiés - optimisé O(n).
    Seul le Sphinx a un comportement spécial (ignore les troupes).
    """

    def __init__(self, pyramid_ids: set[int]):
        super().__init__()
        self.pyramid_ids = set(int(x) for x in pyramid_ids)

    def _get_unit_type(self, stats: UnitStats) -> str:
        """Détermine le type d'unité (S/M/L) basé sur power."""
        power = getattr(stats, 'power', 0)
        if power <= 9:
            return "S"  # Momie
        elif power <= 14:
            return "M"  # Dromadaire
        else:
            return "L"  # Sphinx

    def process(self, dt: float):
        if dt <= 0:
            return

        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            # Vérifier que l'unité est vivante
            if esper.has_component(eid, Health):
                hp = esper.component_for_entity(eid, Health)
                if hp.is_dead:
                    continue

            unit_type = self._get_unit_type(stats)

            # Sphinx: siège - retire la cible si c'est une unité
            if unit_type == "L":
                if esper.has_component(eid, Target):
                    target = esper.component_for_entity(eid, Target)
                    if target.type == "unit":
                        esper.remove_component(eid, Target)
