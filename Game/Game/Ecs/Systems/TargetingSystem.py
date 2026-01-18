import math
import esper

from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.team import Team
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.unitStats import UnitStats
from Game.Ecs.Components.target import Target
from Game.Ecs.Components.pathRequest import PathRequest
from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress


class TargetingSystem(esper.Processor):
    """
    Phase 1 sans IA :
    - Assigne une cible si un ennemi est dans la portée (règle déterministe : le + proche)
    - Si pas de cible et que l'unité est "idle" => redemande un chemin vers la pyramide ennemie
    """

    def __init__(self, *, goals_by_team: dict[int, GridPosition], pyramid_ids: set[int], attack_range: float = 0.85):
        super().__init__()
        self.goals_by_team = goals_by_team
        self.pyramid_ids = set(pyramid_ids)
        self.attack_range = float(attack_range)

    def process(self, dt: float):
        # liste des cibles possibles (vivantes)
        candidates = []
        for eid, (t, team, hp) in esper.get_components(Transform, Team, Health):
            if hp.is_dead:
                continue
            candidates.append((eid, t, team))

        # pour chaque unité
        for eid, (t, team, stats) in esper.get_components(Transform, Team, UnitStats):
            # ignore morts (au cas où)
            if esper.has_component(eid, Health):
                if esper.component_for_entity(eid, Health).is_dead:
                    continue

            ax, ay = t.pos
            best_id = None
            best_dist = 999999.0
            best_type = "entity"

            for cid, ct, cteam in candidates:
                if cid == eid:
                    continue
                if cteam.id == team.id:
                    continue

                bx, by = ct.pos
                d = math.hypot(bx - ax, by - ay)

                if d <= self.attack_range and d < best_dist:
                    best_dist = d
                    best_id = cid
                    best_type = "pyramid" if cid in self.pyramid_ids else "unit"

            # set / unset Target
            if best_id is not None:
                if esper.has_component(eid, Target):
                    tg = esper.component_for_entity(eid, Target)
                    tg.entity_id = int(best_id)
                    tg.type = best_type
                else:
                    esper.add_component(eid, Target(entity_id=int(best_id), type=best_type))
            else:
                if esper.has_component(eid, Target):
                    esper.remove_component(eid, Target)

                # si l'unité n'a plus rien à faire, on la renvoie vers l'objectif de son équipe
                if (not esper.has_component(eid, Path)) and (not esper.has_component(eid, PathRequest)):
                    goal = self.goals_by_team.get(int(team.id))
                    if goal is not None:
                        esper.add_component(eid, PathRequest(goal=GridPosition(goal.x, goal.y)))
                        if esper.has_component(eid, PathProgress):
                            esper.remove_component(eid, PathProgress)
