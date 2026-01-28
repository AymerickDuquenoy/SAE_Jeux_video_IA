import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.speed import Speed
from Game.Ecs.Components.terrain_effect import TerrainEffect


class TerrainEffectSystem:
    """
    Met à jour la vitesse effective selon le terrain sous l'entité.

    Règle :
      - mult = nav_grid.mult[y][x]
      - Speed.mult_terrain = mult

    Important : on ne veut PAS appliquer 2 fois le slow.
    Donc si un composant TerrainEffect existe déjà sur une entité, on l'enlève,
    car NavigationSystem applique déjà TerrainEffect.apply().
    Ici on choisit : "Speed.mult_terrain uniquement".
    """

    # Initialise le système d'effets de terrain avec la grille de navigation
    def __init__(self, nav_grid):
        self.nav_grid = nav_grid

    # Compatible si ton World appelle system.process(dt)
    # Met à jour le multiplicateur de vitesse selon le terrain sous chaque unité
    def process(self, dt: float):
        if not self.nav_grid:
            return

        for ent, (gpos, speed) in esper.get_components(GridPosition, Speed):
            x = int(gpos.x)
            y = int(gpos.y)

            mult = 1.0
            if self.nav_grid.in_bounds(x, y):
                mult = float(self.nav_grid.mult[y][x])

            # garde-fous
            if mult < 0.0:
                mult = 0.0

            speed.mult_terrain = mult

            # évite double application si TerrainEffect existe déjà
            if esper.has_component(ent, TerrainEffect):
                esper.remove_component(ent, TerrainEffect)

    # Compatible si ton World appelle system(world, dt)
    # Permet d'appeler le système avec différentes signatures (compatibilité)
    def __call__(self, world, dt: float):
        self.process(dt)