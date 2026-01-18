import math
import esper
from components import Position, GridPosition, Health, Damage, Target, Pyramid, PathRequest

try:
    from components import AttackRange
    HAS_RANGE = True
except Exception:
    HAS_RANGE = False

try:
    from components import Path, PathProgress
    HAS_PATH = True
except Exception:
    HAS_PATH = False


class CombatSystem(esper.Processor):
    def process(self, dt: float):
        if dt <= 0:
            return

        for ent, (pos, gpos, hp, dmg, tgt) in esper.get_components(
            Position, GridPosition, Health, Damage, Target
        ):
            if hp.hp <= 0 or esper.has_component(ent, Pyramid):
                continue

            if tgt.entity is None or not esper.entity_exists(tgt.entity):
                tgt.entity = None
                continue

            if not (esper.has_component(tgt.entity, Position) and esper.has_component(tgt.entity, Health)):
                tgt.entity = None
                continue

            t_pos = esper.component_for_entity(tgt.entity, Position)
            t_hp = esper.component_for_entity(tgt.entity, Health)
            if t_hp.hp <= 0:
                tgt.entity = None
                continue

            r = 28.0
            if HAS_RANGE and esper.has_component(ent, AttackRange):
                r = max(0.0, esper.component_for_entity(ent, AttackRange).px) or 28.0

            d = math.hypot(t_pos.x - pos.x, t_pos.y - pos.y)

            if d <= r:
                if HAS_PATH:
                    if esper.has_component(ent, Path):
                        esper.remove_component(ent, Path)
                    if esper.has_component(ent, PathProgress):
                        esper.remove_component(ent, PathProgress)

                t_hp.hp -= float(dmg.dps) * dt
                if t_hp.hp < 0:
                    t_hp.hp = 0
            else:
                if esper.has_component(tgt.entity, GridPosition):
                    tg = esper.component_for_entity(tgt.entity, GridPosition)
                    goal = (tg.x, tg.y)
                    if (not esper.has_component(ent, PathRequest)) or (esper.component_for_entity(ent, PathRequest).goal != goal):
                        esper.add_component(ent, PathRequest(start=(gpos.x, gpos.y), goal=goal))
