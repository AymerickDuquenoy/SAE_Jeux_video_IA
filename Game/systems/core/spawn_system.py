import esper
from components import (
    Spawner, Position, GridPosition, Team, Health, Sprite,
    Damage, Pyramid, MoveSpeed, PathRequest, UnitTag
)
from constants import Grid
from game.unit_stats import UNIT_STATS


def enemy_pyramid_goal(team_id: int):
    enemy = 1 - team_id
    for _p_ent, (gpos, t, _pyr) in esper.get_components(GridPosition, Team, Pyramid):
        if t.id == enemy:
            return (gpos.x, gpos.y)
    return None


class SpawnSystem(esper.Processor):
    def process(self, dt: float):
        if dt <= 0:
            return

        for _ent, spawner in esper.get_component(Spawner):
            spawner.timer += dt
            if not spawner.queue:
                continue
            if spawner.timer < spawner.cooldown:
                continue

            unit_type = spawner.queue.pop(0)
            stats = UNIT_STATS[unit_type]

            u = esper.create_entity()

            pos = Position(spawner.x, spawner.y)
            esper.add_component(u, pos)

            gpos = GridPosition(int(pos.x // Grid.TILE_SIZE), int(pos.y // Grid.TILE_SIZE))
            esper.add_component(u, gpos)

            esper.add_component(u, Team(spawner.team_id))   # ⚠️ si ton Spawner garde team_id, ok
            esper.add_component(u, UnitTag(unit_type))

            esper.add_component(u, Health(float(stats["hp"]), float(stats["hp"])))
            esper.add_component(u, Damage(float(stats["damage"])))
            esper.add_component(u, Sprite(40, 40, stats["color"]))

            pxps = 60.0 + float(stats["speed"]) * 20.0
            esper.add_component(u, MoveSpeed(pxps))

            goal = enemy_pyramid_goal(esper.component_for_entity(u, Team).id)
            if goal is not None:
                esper.add_component(u, PathRequest(start=(gpos.x, gpos.y), goal=goal))

            spawner.timer = 0.0
