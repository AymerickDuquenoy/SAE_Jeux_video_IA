import esper

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.pathRequest import PathRequest
from Game.Ecs.Components.path import Path
from Game.Ecs.Components.pathProgress import PathProgress
from Game.Ecs.Systems.AStarPathfindingSystem import AStarPathfindingSystem
from Game.Services.NavigationGrid import NavigationGrid


def main():
    grid = NavigationGrid(10, 8)

    # obstacles
    for x in range(3, 7):
        grid.set_cell(x, 3, walkable=False)

    # zone lente
    for y in range(5, 8):
        grid.set_cell(5, y, mult=0.5)

    esper.add_processor(AStarPathfindingSystem(grid))

    eid = esper.create_entity(
        GridPosition(1, 1),
        PathRequest(goal=GridPosition(8, 6))
    )

    esper.process(0.016)

    if esper.has_component(eid, Path):
        path = esper.component_for_entity(eid, Path)
        print("Chemin trouvé :")
        print([(p.x, p.y) for p in path.noeuds])

        prog = esper.component_for_entity(eid, PathProgress)
        print("Index initial PathProgress =", prog.index)
    else:
        print("Aucun chemin trouvé.")


if __name__ == "__main__":
    main()
