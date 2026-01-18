import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.pathRequest import PathRequest
from Game.Ecs.Components.transform import Transform
from Game.Ecs.Systems.AStarPathfindingSystem import AStarPathfindingSystem
from Game.Ecs.Systems.NavigationSystem import NavigationSystem
from Game.Services.NavigationGrid import NavigationGrid


def main():
    grid = NavigationGrid(10, 8)

    # obstacles
    for x in range(3, 7):
        grid.set_cell(x, 3, walkable=False)

    dt = 1 / 60

    esper.add_processor(AStarPathfindingSystem(grid))
    esper.add_processor(NavigationSystem(max_accel=10.0))

    eid = esper.create_entity(
        GridPosition(1, 1),
        PathRequest(goal=GridPosition(8, 6))
    )

    # tick 1 : calcule le path
    esper.process(dt)

    # ticks suivants : navigation
    for _ in range(300):
        esper.process(dt)

    t = esper.component_for_entity(eid, Transform)
    print("Position finale :", t.pos)


if __name__ == "__main__":
    main()
