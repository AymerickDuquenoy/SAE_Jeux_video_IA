import esper
from components import Position, GridPosition
from constants import Grid


class GridSyncSystem(esper.Processor):
    def process(self, dt: float):
        for _e, (pos, gpos) in esper.get_components(Position, GridPosition):
            gpos.x = int(pos.x // Grid.TILE_SIZE)
            gpos.y = int(pos.y // Grid.TILE_SIZE)
