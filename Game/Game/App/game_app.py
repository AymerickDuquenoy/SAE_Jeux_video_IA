from Game.App.game_boot import GameBoot
from Game.App.game_map import GameMap
from Game.App.game_lanes import GameLanes
from Game.App.game_ui import GameUI
from Game.App.game_match import GameMatch
from Game.App.game_draw import GameDraw
from Game.App.game_save import GameSave


class GameApp:
    def __init__(self, width=960, height=640, title="Antique War"):
        self.width = width
        self.height = height
        self.title = title


        self.boot = GameBoot(self)
        self.save = GameSave(self)
        self.map = GameMap(self)
        self.lanes = GameLanes(self)
        self.ui = GameUI(self)
        self.match = GameMatch(self)
        self.draw = GameDraw(self)


    def run(self):
        self.boot.boot()
        while self.boot.running:
            self.boot.tick()
            self.ui.handle_events()
            self.match.update()
            self.draw.render()
        self.boot.shutdown()