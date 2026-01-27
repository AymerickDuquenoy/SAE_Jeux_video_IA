from Game.Services.GridMap import GridMap
from Game.Services.NavigationGrid import NavigationGrid
from Game.Services.GridTile import GridTile


class GameMap:
    def __init__(self, app):
        self.app = app
        self.game_map = None
        self.nav_grid = None


    def load_visual(self, path):
        self.game_map = GridMap(str(path))


    def build_nav(self):
        nav = NavigationGrid(self.game_map.width, self.game_map.height)
        vmax = float(getattr(GridTile, "VITESSE_MAX", 10.0))
        for t in self.game_map.tiles:
            speed = getattr(t, "speed", vmax)
            nav.set_cell(t.x, t.y, t.walkable, speed / vmax)
        self.nav_grid = nav