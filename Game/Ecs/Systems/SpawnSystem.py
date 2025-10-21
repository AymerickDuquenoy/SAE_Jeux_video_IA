
from collections import deque
import esper
from Components.grid_position import GridPosition
from Components.pathRequest import PathRequest

class SpawnSystem(esper.Processor):
    """Spawner minimal : enqueue → process → create_unit + PathRequest."""
    def __init__(self, entity_factory):
        self.factory = entity_factory  # doit exposer: create_unit(world, unit_type, team, tile_pos, **overrides)
        self._queue = deque()

    def spawn(self, *, unit_type: str, team: int, start: tuple[int,int], goal: tuple[int,int], **overrides):
        """Ajoute une demande de spawn (appelée depuis l'UI ou un script)."""
        self._queue.append((unit_type, team, start, goal, overrides))

    def process(self, dt: float):
        while self._queue:
            unit_type, team, (sx, sy), (gx, gy), overrides = self._queue.popleft()
            eid = self.factory.create_unit(
                self.world, unit_type=unit_type, team=team, tile_pos=(sx, sy), **overrides
            )
            self.world.add_component(eid, PathRequest(goal=GridPosition(gx, gy)))
