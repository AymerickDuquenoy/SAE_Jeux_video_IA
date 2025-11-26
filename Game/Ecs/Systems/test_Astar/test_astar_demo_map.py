"""Demo map with mixed terrain types for A* visual testing.

This script creates a procedural map with different terrain types:
- Desert (speed 10, walkable)
- Sables mouvants / Quicksand (speed 5, walkable but slow)
- Pyramide / Camp / Obstacles (not walkable)
- Cactus / Trees (not walkable)

Then displays it with A* pathfinding overlay using Pygame.

Left-click: set START (green)
Right-click: set GOAL (blue)
Path shown in red.
"""
import pygame
import random


class DemoTile:
    """Mock tile matching GridTile interface."""
    def __init__(self, x, y, terrain_type):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.walkable = True
        self.speed = 10.0
        self.image = None
        self._apply_rules()

    def _apply_rules(self):
        if self.terrain_type in ["desert"]:
            self.walkable = True
            self.speed = 10.0
        elif self.terrain_type in ["sables_mouvants", "quicksand"]:
            self.walkable = True
            self.speed = 5.0
        elif self.terrain_type in ["pyramide", "camp"]:
            self.walkable = False
            self.speed = 0
        elif self.terrain_type in ["cactus", "palmier"]:
            self.walkable = False
            self.speed = 0
        else:
            self.walkable = True
            self.speed = 10.0


class DemoGridMap:
    """Mock GridMap for demo."""
    def __init__(self, width, height, tiles):
        self.width = width
        self.height = height
        self.tiles = tiles
        self.tilewidth = 32
        self.tileheight = 32


def generate_demo_map(width=30, height=20):
    """Generate a procedural map with mixed terrain types."""
    tiles = []
    random.seed(42)

    for y in range(height):
        for x in range(width):
            r = random.random()
            if r < 0.15:
                terrain = "pyramide"
            elif r < 0.25:
                terrain = "cactus"
            elif r < 0.35:
                terrain = "sables_mouvants"
            else:
                terrain = "desert"

            tile = DemoTile(x, y, terrain)
            tiles.append(tile)

    return DemoGridMap(width, height, tiles)


def load_astar():
    import sys
    import os
    # Add parent directory to path so we can import AStarPathfindingSystem
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    import AStarPathfindingSystem
    return AStarPathfindingSystem


def main():
    pygame.init()
    astar_mod = load_astar()

    # Generate demo map
    grid_map = generate_demo_map(30, 20)

    tile_w = grid_map.tilewidth
    tile_h = grid_map.tileheight
    screen_w = 960
    screen_h = 640
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
    pygame.display.set_caption('A* Demo Map - Mixed Terrains')

    start = (1, 1)
    goal = (grid_map.width - 2, grid_map.height - 2)
    path = astar_mod.astar(grid_map, start, goal, allow_diagonal=False)

    clock = pygame.time.Clock()
    running = True
    cam_x = cam_y = 0

    font = pygame.font.SysFont(None, 20)
    font_tiny = pygame.font.SysFont(None, 11)
    font_small = pygame.font.SysFont(None, 14)

    # Terrain colors (lighter and less opaque)
    terrain_colors = {
        'desert': (255, 200, 100, 60),          # lighter sandy
        'sables_mouvants': (255, 230, 100, 70), # brighter yellow
        'quicksand': (255, 230, 100, 70),       # brighter yellow
        'pyramide': (220, 150, 150, 70),        # lighter red
        'camp': (220, 150, 150, 70),            # lighter red
        'cactus': (150, 200, 150, 70),          # lighter green
        'palmier': (150, 200, 150, 70),         # lighter green
    }

    terrain_abbr_map = {
        'desert': 'D',
        'sables_mouvants': 'S',
        'quicksand': 'S',
        'pyramide': 'P',
        'camp': 'C',
        'cactus': 'X',
        'palmier': 'T',
    }

    # Build terrain info
    terrain_info = {}
    for tile in grid_map.tiles:
        terrain_info[(tile.x, tile.y)] = {
            'type': tile.terrain_type,
            'walkable': tile.walkable,
            'speed': tile.speed
        }

    hovered_tile = None

    # Overlay surfaces
    overlay_surf = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
    overlay_surf.fill((255, 0, 0, 100))  # path: red
    start_surf = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
    start_surf.fill((0, 255, 0, 160))    # start: green
    goal_surf = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
    goal_surf.fill((0, 0, 255, 160))     # goal: blue

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                tx = (mx + cam_x) // tile_w
                ty = (my + cam_y) // tile_h
                if 0 <= tx < grid_map.width and 0 <= ty < grid_map.height:
                    if event.button == 1:  # left -> start
                        start = (tx, ty)
                        path = astar_mod.astar(grid_map, start, goal, allow_diagonal=False)
                    elif event.button == 3:  # right -> goal
                        goal = (tx, ty)
                        path = astar_mod.astar(grid_map, start, goal, allow_diagonal=False)

        mx, my = pygame.mouse.get_pos()
        tx = (mx + cam_x) // tile_w
        ty = (my + cam_y) // tile_h
        hovered_tile = (tx, ty) if (0 <= tx < grid_map.width and 0 <= ty < grid_map.height) else None

        # Draw
        screen.fill((0, 0, 0))

        # Draw tiles with terrain colors
        for tile in grid_map.tiles:
            px = tile.x * tile_w - cam_x
            py = tile.y * tile_h - cam_y
            if -tile_w < px < screen_w and -tile_h < py < screen_h:
                # Terrain color overlay
                color = terrain_colors.get(tile.terrain_type, (100, 100, 100, 20))
                if color:
                    ov = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
                    ov.fill(color)
                    screen.blit(ov, (px, py))

                # Terrain abbreviation
                abbr = terrain_abbr_map.get(tile.terrain_type, '?')
                label_color = (0, 0, 0) if not tile.walkable else (50, 50, 50)
                txt = font_tiny.render(abbr, True, label_color)
                screen.blit(txt, (px + tile_w // 2 - 3, py + tile_h // 2 - 6))

        # Draw path
        if path:
            for (x, y) in path:
                px = x * tile_w - cam_x
                py = y * tile_h - cam_y
                if -tile_w < px < screen_w and -tile_h < py < screen_h:
                    screen.blit(overlay_surf, (px, py))

        # Draw start/goal
        sx = start[0] * tile_w - cam_x
        sy = start[1] * tile_h - cam_y
        gx = goal[0] * tile_w - cam_x
        gy = goal[1] * tile_h - cam_y
        screen.blit(start_surf, (sx, sy))
        screen.blit(goal_surf, (gx, gy))

        # HUD
        info = f'Start={start}  Goal={goal}  PathLen={len(path) if path else "No path"}  Left=start, Right=goal'
        txt = font.render(info, True, (255, 255, 255))
        screen.blit(txt, (5, 5))

        legend_y = 30
        legend = [
            "Legend: D=Desert(s=10) | S=Quicksand(s=5) | P=Pyramid(blocked) | X=Cactus(blocked)",
            "Green=Start | Blue=Goal | Red=Path"
        ]
        for i, leg in enumerate(legend):
            txt_leg = font_small.render(leg, True, (200, 200, 200))
            screen.blit(txt_leg, (5, legend_y + i * 20))

        # Hover info
        if hovered_tile and hovered_tile in terrain_info:
            tinfo = terrain_info[hovered_tile]
            info_hover = f"Tile {hovered_tile}: {tinfo['type']} | Speed: {tinfo['speed']} | Walkable: {tinfo['walkable']}"
            txt_hover = font_small.render(info_hover, True, (255, 255, 0))
            screen.blit(txt_hover, (5, screen_h - 25))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == '__main__':
    main()
