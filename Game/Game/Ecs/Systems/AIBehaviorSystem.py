"""
AIBehaviorSystem - Comportements IA différenciés par type d'unité.

TOUTES les unités combattent les ennemis sur leur lane :
- Momie (S): Combat sur sa lane
- Dromadaire (M): Combat sur sa lane  
- Sphinx (L): Combat sur sa lane (comme les autres)

Version optimisée O(n).
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
    Toutes les unités ont le même comportement de combat.
    """

    # Initialise le système IA avec la liste des pyramides protégées
    def __init__(self, pyramid_ids: set[int]):
        super().__init__()
        self.pyramid_ids = set(int(x) for x in pyramid_ids)

    # Traite le comportement IA (actuellement délégué à d'autres systèmes)
    def process(self, dt: float):
        # Ce système ne fait plus rien de spécial
        # Le ciblage et le combat sont gérés par TargetingSystem et CombatSystem
        pass