class GameLanes:
    def __init__(self, app):
        self.app = app
        self.lanes_y = [0, 0, 0]
        self.lane_paths = [[], [], []]
        self.lane_paths_enemy = [[], [], []]


    def recalculate(self):
        # appel A* et recalcul
        pass