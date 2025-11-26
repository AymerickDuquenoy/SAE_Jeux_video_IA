"""Visual A* test using your `GridMap` and `AStar`.

Features:
- Loads the TMX via `GridMap` (no modification to project files).
- Computes a path with `AStar.astar(grid_map, start, goal, ...)`.
- Displays the map background and overlays the path.
- Left-click to set START, right-click to set GOAL and recompute path.

Run from project root:
    python Game/Services/test_astar_visual.py

Make sure `pytmx` and `pygame` are installed and `Game/assets/map/map.tmx` exists.
"""
import os
import sys
import importlib.util
import pygame


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HERE = os.path.dirname(os.path.abspath(__file__))
# Paths to modules in Game/Services/ and Game/Ecs/Systems/
services_dir = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'Services'))
systems_dir = os.path.normpath(os.path.join(HERE, '..'))
gridmap_path = os.path.join(services_dir, 'GridMap.py')
astar_path = os.path.join(systems_dir, 'AStarPathfindingSystem.py')

# Add directories to sys.path so modules can import their dependencies
if services_dir not in sys.path:
    sys.path.insert(0, services_dir)
if systems_dir not in sys.path:
    sys.path.insert(0, systems_dir)

GridMapMod = load_module(gridmap_path, 'GridMap_mod')
AStarMod = load_module(astar_path, 'AStar_mod')

# Attempt to locate the TMX map
map_file = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'assets', 'map', 'map.tmx'))
if not os.path.exists(map_file):
    print('Map file not found:', map_file)
    sys.exit(1)


def main():
    pygame.init()

    # Initialize display first (required for pytmx to convert images)
    screen_temp = pygame.display.set_mode((100, 100))
    pygame.display.set_caption('Loading...')

    # Load map
    grid_map = GridMapMod.GridMap(map_file)

    # Compute window size from map size (clamp to a reasonable window)
    tile_w = grid_map.tilewidth
    tile_h = grid_map.tileheight
    width_px = grid_map.width * tile_w
    height_px = grid_map.height * tile_h
    screen_w = min(width_px, 1200)
    screen_h = min(height_px, 800)
    # Resize the display to actual needed size
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
    pygame.display.set_caption('A* Visual Test - click to set start/goal')

    # Camera offsets to center or crop if map larger than window
    cam_x = 0
    cam_y = 0

    # default start/goal (tile coords)
    start = (0, 0)
    goal = (grid_map.width - 1, grid_map.height - 1)

    path = AStarMod.astar(grid_map, start, goal, allow_diagonal=False)

    clock = pygame.time.Clock()
    running = True

    overlay_surf = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
    overlay_surf.fill((255, 0, 0, 100))  # semi-transparent red

    start_surf = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
    start_surf.fill((0, 255, 0, 160))

    goal_surf = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
    goal_surf.fill((0, 0, 255, 160))

    font = pygame.font.SysFont(None, 20)
    font_small = pygame.font.SysFont(None, 16)
    font_tiny = pygame.font.SysFont(None, 12)

    # Build terrain info by (x, y) for quick lookup
    terrain_info = {}
    for tile in grid_map.tiles:
        terrain_info[(tile.x, tile.y)] = {
            'type': tile.terrain_type,
            'walkable': tile.walkable,
            'speed': tile.speed
        }

    hovered_tile = None

    # Define terrain colors (semi-transparent overlays)
    terrain_colors = {
        'desert': (200, 170, 100, 40),           # brownish
        'sables_mouvants': (255, 200, 0, 50),    # yellow/gold
        'sables mouvants': (255, 200, 0, 50),    # yellow/gold
        'quicksand': (255, 200, 0, 50),          # yellow/gold
        'pyramide': (100, 50, 50, 60),           # dark red (blocked)
        'camp': (150, 50, 50, 60),               # red (blocked)
        'camp ennemi': (150, 50, 50, 60),        # red (blocked)
        'cactus': (100, 150, 100, 60),           # green (blocked)
        'palmier': (100, 150, 100, 60),          # green (blocked)
        'palm tree': (100, 150, 100, 60),        # green (blocked)
    }

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                tx = (mx + cam_x) // tile_w
                ty = (my + cam_y) // tile_h
                if 0 <= tx < grid_map.width and 0 <= ty < grid_map.height:
                    if event.button == 1:  # left click -> set start
                        start = (tx, ty)
                        path = AStarMod.astar(grid_map, start, goal, allow_diagonal=False)
                    elif event.button == 3:  # right click -> set goal
                        goal = (tx, ty)
                        path = AStarMod.astar(grid_map, start, goal, allow_diagonal=False)
        
        # Track mouse hover for terrain info
        mx, my = pygame.mouse.get_pos()
        tx = (mx + cam_x) // tile_w
        ty = (my + cam_y) // tile_h
        hovered_tile = (tx, ty) if (0 <= tx < grid_map.width and 0 <= ty < grid_map.height) else None

        # Draw background map
        screen.fill((0, 0, 0))
        # Draw all tiles via GridMap.draw (it uses camera offsets)
        grid_map.draw(screen, cam_x, cam_y)

        # Draw terrain type overlays FIRST (semi-transparent colors)
        for tile in grid_map.tiles:
            px = tile.x * tile_w - cam_x
            py = tile.y * tile_h - cam_y
            if -tile_w < px < screen_w and -tile_h < py < screen_h:
                color = terrain_colors.get(tile.terrain_type, (100, 100, 100, 20))
                if color:
                    overlay = pygame.Surface((tile_w, tile_h), flags=pygame.SRCALPHA)
                    overlay.fill(color)
                    screen.blit(overlay, (px, py))
                
                # Draw terrain type abbreviation on tile
                terrain_abbr = {
                    'desert': 'D',
                    'sables_mouvants': 'S',
                    'sables mouvants': 'S',
                    'quicksand': 'S',
                    'pyramide': 'P',
                    'camp': 'C',
                    'camp ennemi': 'E',
                    'cactus': 'X',
                    'palmier': 'T',
                    'palm tree': 'T',
                }.get(tile.terrain_type, '?')
                
                label_color = (0, 0, 0) if not tile.walkable else (50, 50, 50)
                txt = font_tiny.render(terrain_abbr, True, label_color)
                screen.blit(txt, (px + tile_w // 2 - 3, py + tile_h // 2 - 6))

        # Draw path overlay (on top of terrain colors)
        if path:
            for (x, y) in path:
                px = x * tile_w - cam_x
                py = y * tile_h - cam_y
                # if on screen
                if -tile_w < px < screen_w and -tile_h < py < screen_h:
                    screen.blit(overlay_surf, (px, py))

        # Draw start/goal markers (on top of everything)
        sx = start[0] * tile_w - cam_x
        sy = start[1] * tile_h - cam_y
        gx = goal[0] * tile_w - cam_x
        gy = goal[1] * tile_h - cam_y
        screen.blit(start_surf, (sx, sy))
        screen.blit(goal_surf, (gx, gy))

        # HUD
        info = f'Start={start}  Goal={goal}  PathLen={len(path) if path else 0}  Left click=set start, Right click=set goal'
        txt = font.render(info, True, (255, 255, 255))
        screen.blit(txt, (5, 5))

        # Show terrain info on hover
        if hovered_tile and hovered_tile in terrain_info:
            tinfo = terrain_info[hovered_tile]
            hover_text = f"Tile {hovered_tile}: {tinfo['type']} | Speed: {tinfo['speed']} | Walkable: {tinfo['walkable']}"
            txt_hover = font_small.render(hover_text, True, (255, 255, 0))
            screen.blit(txt_hover, (5, screen_h - 25))
        
        # Legend
        legend_y = 30
        legend_texts = [
            "Legend: D=Desert (s=10) | S=Sables mouvants (s=5) | P=Pyramide (blocked)",
            "C=Camp (blocked) | E=Enemy camp (blocked) | X=Cactus (blocked) | T=Tree (blocked)"
        ]
        for i, leg_txt in enumerate(legend_texts):
            txt_leg = font_small.render(leg_txt, True, (200, 200, 200))
            screen.blit(txt_leg, (5, legend_y + i * 20))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == '__main__':
    main()
