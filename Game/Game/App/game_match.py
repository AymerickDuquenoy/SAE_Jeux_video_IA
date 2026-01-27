from Game.Ecs.world import World
from Game.Factory.entity_factory import EntityFactory


class GameMatch:
    def __init__(self, app):
        self.app = app
        self.world = None
        self.factory = None


    def setup(self):
        self.world = World("match")
        self.factory = EntityFactory(self.world)


    def teardown(self):
        self.world = None


    def update(self):
        if self.world:
            self.world.process()