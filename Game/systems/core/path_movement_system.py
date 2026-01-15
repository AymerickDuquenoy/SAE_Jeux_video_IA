import math
import esper
from components import Position, GridPosition, MoveSpeed, Path, PathProgress
from constants import Grid


class PathMovementSystem(esper.Processor):
    def __init__(self):
        self.snap_dist = 2.0

    def process(self, dt: float):
        if dt <= 0:
            return

        for ent, (pos, gpos, speed, path, prog) in esper.get_components(
            Position, GridPosition, MoveSpeed, Path, PathProgress
        ):
            if prog.index >= len(path.nodes):
                esper.remove_component(ent, Path)
                esper.remove_component(ent, PathProgress)
                continue

            tx, ty = path.nodes[prog.index]
            target_x = tx * Grid.TILE_SIZE + Grid.TILE_SIZE * 0.5
            target_y = ty * Grid.TILE_SIZE + Grid.TILE_SIZE * 0.5

            dx = target_x - pos.x
            dy = target_y - pos.y
            dist = math.hypot(dx, dy)

            if dist <= self.snap_dist:
                pos.x = target_x
                pos.y = target_y
                prog.index += 1
            else:
                step = speed.px_per_sec * dt
                if step >= dist:
                    pos.x = target_x
                    pos.y = target_y
                    prog.index += 1
                else:
                    pos.x += (dx / dist) * step
                    pos.y += (dy / dist) * step

            gpos.x = int(pos.x // Grid.TILE_SIZE)
            gpos.y = int(pos.y // Grid.TILE_SIZE)
