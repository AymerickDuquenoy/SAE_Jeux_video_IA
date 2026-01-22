# Game/App/match_manager.py
"""
Match lifecycle management for Antique War.
Handles setup, teardown, and state management for game matches.
"""

import random
import heapq
from pathlib import Path

import esper

from Game.Ecs.world import World
from Game.Services.NavigationGrid import NavigationGrid
from Game.Services.GridMap import GridMap
from Game.Services.GridTile import GridTile
from Game.Services.terrain_randomizer import apply_random_terrain
from Game.Factory.entity_factory import EntityFactory

from Game.Ecs.Components.grid_position import GridPosition
from Game.Ecs.Components.transform import Transform
from Game.Ecs.Components.path import Path as PathComponent
from Game.Ecs.Components.pathProgress import PathProgress

from Game.App.map_generator import generate_tmx_map, get_default_map_config
from Game.App.constants import DEFAULT_LANE_INDEX


class MatchManager:
    """
    Manages the lifecycle of a game match.
    Handles setup, teardown, navigation grid, and lane calculations.
    """
    
    def __init__(self, game_root: Path, balance: dict):
        self.game_root = game_root
        self.balance = balance
        
        # Match state
        self.match_index = 0
        self.world = None
        self.factory = None
        
        # Map and navigation
        self.game_map = None
        self.nav_grid = None
        
        # Entities
        self.player_pyramid_eid = None
        self.enemy_pyramid_eid = None
        
        # Positions
        self.player_pyr_pos = (0, 0)
        self.enemy_pyr_pos = (0, 0)
        
        # Lanes
        self.lanes_y = [0, 0, 0]
        self.lane_paths = [[], [], []]
        self.selected_lane_idx = DEFAULT_LANE_INDEX
        
        # Map info
        self.last_map_seed = 0
        self.last_zone_counts = {"open": 0, "dusty": 0, "forbidden": 0}
        self.last_map_name = "map.tmx"
        
        # Systems (stored for reference)
        self.systems = {}
    
    def setup_match(self) -> dict:
        """
        Set up a new match.
        
        Returns:
            Dictionary containing system references for the main app.
        """
        self.match_index += 1
        self.selected_lane_idx = DEFAULT_LANE_INDEX
        
        # Generate map seed
        self.last_map_seed = int(random.randint(1, 2_000_000_000))
        
        # Load or generate map
        self._setup_map()
        
        # Build navigation grid
        self._setup_navigation()
        
        # Calculate lanes
        self._setup_lanes()
        
        # Apply random terrain (SAÉ zones)
        self._apply_terrain_randomization()
        
        # Carve pyramid connectors
        self._carve_pyramid_connectors()
        
        # Calculate lane paths
        self._calculate_lane_paths()
        
        # Create world and entities
        self._setup_world()
        
        # Create and register systems
        self._setup_systems()
        
        return self.systems
    
    def teardown_match(self):
        """Clean up match state."""
        self.world = None
        self.factory = None
        
        self.player_pyramid_eid = None
        self.enemy_pyramid_eid = None
        
        self.lane_paths = [[], [], []]
        self.systems = {}
    
    # =========================================================================
    # PRIVATE SETUP METHODS
    # =========================================================================
    
    def _setup_map(self):
        """Load or generate the game map."""
        maps_dir = self.game_root / "assets" / "map"
        map_files = sorted(maps_dir.glob("map_*.tmx"))
        
        if not map_files:
            map_files = [maps_dir / "map.tmx"]
        
        use_generated = (len(map_files) == 1 and map_files[0].name == "map.tmx")
        
        if use_generated:
            gen_path = maps_dir / "_generated.tmx"
            config = get_default_map_config(self.balance)
            
            generate_tmx_map(
                gen_path,
                seed=self.last_map_seed,
                width=config["width"],
                height=config["height"],
                tilewidth=config["tilewidth"],
                tileheight=config["tileheight"],
                quicksand_rects=config["dusty_rects"],
            )
            
            chosen = gen_path
        else:
            chosen = random.choice(map_files)
        
        self.last_map_name = chosen.name
        self.game_map = GridMap(str(chosen))
    
    def _setup_navigation(self):
        """Build navigation grid from map."""
        self.nav_grid = NavigationGrid(
            int(self.game_map.width),
            int(self.game_map.height)
        )
        
        vmax = float(getattr(GridTile, "VITESSE_MAX", 10.0))
        
        # Copy tile properties to nav grid
        for t in getattr(self.game_map, "tiles", []):
            speed = float(getattr(t, "speed", vmax))
            walkable = bool(getattr(t, "walkable", True))
            mult = 0.0 if speed <= 0 else max(0.0, min(1.0, speed / vmax))
            self.nav_grid.set_cell(int(t.x), int(t.y), walkable=walkable, mult=mult)
        
        # Mark borders as forbidden
        w = self.nav_grid.width
        h = self.nav_grid.height
        
        for x in range(w):
            self.nav_grid.set_cell(x, 0, walkable=False, mult=0.0)
            self.nav_grid.set_cell(x, h - 1, walkable=False, mult=0.0)
        for y in range(h):
            self.nav_grid.set_cell(0, y, walkable=False, mult=0.0)
            self.nav_grid.set_cell(w - 1, y, walkable=False, mult=0.0)
    
    def _setup_lanes(self):
        """Calculate lane Y positions based on pyramid position."""
        mp = self.balance.get("map", {})
        
        # Get pyramid positions
        self.player_pyr_pos = self._find_walkable_near(*mp.get("player_pyramid", [2, 10]))
        self.enemy_pyr_pos = self._find_walkable_near(*mp.get("enemy_pyramid", [27, 10]))
        
        # Calculate lanes (relative to player pyramid)
        h = self.nav_grid.height
        base_y = int(self.player_pyr_pos[1])
        spacing = 1
        
        l2 = self._clamp(base_y, 1, h - 2)
        l1 = self._clamp(base_y - spacing, 1, h - 2)
        l3 = self._clamp(base_y + spacing, 1, h - 2)
        
        self.lanes_y = [l1, l2, l3]
    
    def _apply_terrain_randomization(self):
        """Apply SAÉ terrain randomization (dusty/forbidden zones)."""
        mp = self.balance.get("map", {})
        rng = random.Random(self.last_map_seed + 1337)
        
        # Protected positions (pyramids, spawns, lane entries)
        protect = []
        for key in ("player_pyramid", "enemy_pyramid", "player_spawn", "enemy_spawn"):
            if key in mp:
                protect.append(tuple(mp[key]))
        
        protect.append(tuple(self.player_pyr_pos))
        protect.append(tuple(self.enemy_pyr_pos))
        
        w = self.nav_grid.width
        for ly in self.lanes_y:
            px = int(self.player_pyr_pos[0])
            ex = int(self.enemy_pyr_pos[0])
            entry_p = (self._clamp(px + 1, 1, w - 2), int(ly))
            entry_e = (self._clamp(ex - 1, 1, w - 2), int(ly))
            protect.append(entry_p)
            protect.append(entry_e)
        
        dusty_div = float(self.balance.get("sae", {}).get("dusty_divisor", 2.0))
        dusty_rects = int(mp.get("dusty_rects", 7))
        forbidden_rects = int(mp.get("forbidden_rects", 3))
        
        self.last_zone_counts = apply_random_terrain(
            self.nav_grid,
            lanes_y=self.lanes_y,
            protected_positions=protect,
            rng=rng,
            dusty_divisor=dusty_div,
            dusty_rects=dusty_rects,
            forbidden_rects=forbidden_rects,
            corridor_half_height=1,
        )
    
    def _carve_pyramid_connectors(self):
        """Ensure pyramids are accessible from all lanes."""
        if not self.nav_grid:
            return
        
        w = self.nav_grid.width
        h = self.nav_grid.height
        if w <= 0 or h <= 0:
            return
        
        px, py = int(self.player_pyr_pos[0]), int(self.player_pyr_pos[1])
        ex, ey = int(self.enemy_pyr_pos[0]), int(self.enemy_pyr_pos[1])
        
        # Vertical corridors near pyramids
        col_player = self._clamp(px + 1, 1, w - 2)
        col_enemy = self._clamp(ex - 1, 1, w - 2)
        
        ymin = max(1, min(self.lanes_y + [py, ey]))
        ymax = min(h - 2, max(self.lanes_y + [py, ey]))
        
        for y in range(ymin, ymax + 1):
            self._force_open_cell(col_player, y)
            self._force_open_cell(col_enemy, y)
        
        # Lane entry points
        for ly in self.lanes_y:
            self._force_open_cell(col_player, int(ly))
            self._force_open_cell(col_enemy, int(ly))
        
        # Attack cells for each lane
        for lane_idx in range(3):
            ax1, ay1 = self.get_attack_cell(1, lane_idx)
            ax2, ay2 = self.get_attack_cell(2, lane_idx)
            self._force_open_cell(ax1, ay1)
            self._force_open_cell(ax2, ay2)
        
        # Padding around pyramids
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            self._force_open_cell(self._clamp(px + dx, 1, w - 2), self._clamp(py + dy, 1, h - 2))
            self._force_open_cell(self._clamp(ex + dx, 1, w - 2), self._clamp(ey + dy, 1, h - 2))
        
        # Connectors around enemy pyramid for lane 1/3
        for (xx, yy) in [(ex - 1, ey - 1), (ex - 1, ey + 1), (ex, ey - 1), (ex, ey + 1)]:
            if 1 <= xx < w - 1 and 1 <= yy < h - 1:
                self._force_open_cell(xx, yy)
        
        # Connectors around player pyramid
        for (xx, yy) in [(px + 1, py - 1), (px + 1, py + 1), (px, py - 1), (px, py + 1)]:
            if 1 <= xx < w - 1 and 1 <= yy < h - 1:
                self._force_open_cell(xx, yy)
    
    def _calculate_lane_paths(self):
        """Pre-calculate A* paths for all three lanes."""
        self.lane_paths = [
            self._compute_lane_route_path(0),
            self._compute_lane_route_path(1),
            self._compute_lane_route_path(2),
        ]
    
    def _setup_world(self):
        """Create ECS world and pyramid entities."""
        self.world = World(name=f"match_{self.match_index}")
        
        tile_size = int(self.game_map.tilewidth)
        self.factory = EntityFactory(self.world, tile_size=tile_size, balance=self.balance)
        
        self.player_pyramid_eid = self.factory.create_pyramid(
            team_id=1,
            grid_pos=tuple(self.player_pyr_pos)
        )
        self.enemy_pyramid_eid = self.factory.create_pyramid(
            team_id=2,
            grid_pos=tuple(self.enemy_pyr_pos)
        )
    
    def _setup_systems(self):
        """Create and register all ECS systems."""
        from Game.Ecs.Systems.input_system import InputSystem
        from Game.Ecs.Systems.AStarPathfindingSystem import AStarPathfindingSystem
        from Game.Ecs.Systems.TerrainEffectSystem import TerrainEffectSystem
        from Game.Ecs.Systems.NavigationSystem import NavigationSystem
        from Game.Ecs.Systems.TargetingSystem import TargetingSystem
        from Game.Ecs.Systems.CombatSystem import CombatSystem
        from Game.Ecs.Systems.ProjectileSystem import ProjectileSystem
        from Game.Ecs.Systems.CleanupSystem import CleanupSystem
        from Game.Ecs.Systems.EconomySystem import EconomySystem
        from Game.Ecs.Systems.UpgradeSystem import UpgradeSystem
        from Game.Ecs.Systems.LaneRouteSystem import LaneRouteSystem
        from Game.Ecs.Systems.EnemySpawnerSystem import EnemySpawnerSystem
        from Game.Ecs.Systems.DifficultySystem import DifficultySystem
        
        pyramid_ids = {int(self.player_pyramid_eid), int(self.enemy_pyramid_eid)}
        
        # Input system
        input_system = InputSystem(
            self.factory,
            self.balance,
            self.player_pyramid_eid,
            self.enemy_pyramid_eid,
            self.nav_grid,
            lanes_y=self.lanes_y,
        )
        
        # Economy system
        default_income = float(self.balance.get("pyramid", {}).get("income_base", 2.0))
        economy_system = EconomySystem(
            player_pyramid_eid=self.player_pyramid_eid,
            default_income=default_income
        )
        
        # Upgrade system
        upgrade_costs = self.balance.get("pyramid", {}).get("upgrade_costs", [100.0])
        base_upgrade_cost = float(upgrade_costs[0]) if isinstance(upgrade_costs, list) and len(upgrade_costs) else 100.0
        upgrade_system = UpgradeSystem(
            player_pyramid_eid=self.player_pyramid_eid,
            base_cost=base_upgrade_cost
        )
        
        # Pathfinding systems
        astar_system = AStarPathfindingSystem(self.nav_grid)
        terrain_system = TerrainEffectSystem(self.nav_grid)
        nav_system = NavigationSystem(arrive_radius=0.05)
        
        # Lane route system
        lane_route_system = LaneRouteSystem(
            self.nav_grid,
            self.lanes_y,
            self.player_pyr_pos,
            self.enemy_pyr_pos,
            pyramid_ids=pyramid_ids
        )
        
        # Combat systems
        goal_team1 = self.get_attack_cell(1, 1)  # Middle lane
        goal_team2 = self.get_attack_cell(2, 1)
        
        goals_by_team = {
            1: GridPosition(int(goal_team1[0]), int(goal_team1[1])),
            2: GridPosition(int(goal_team2[0]), int(goal_team2[1])),
        }
        
        targeting_system = TargetingSystem(
            goals_by_team=goals_by_team,
            pyramid_ids=pyramid_ids,
            attack_range=1.25
        )
        
        combat_system = CombatSystem(
            attack_range=1.25,
            hit_cooldown=0.7,
            projectile_speed=10.0
        )
        
        reward_divisor = float(self.balance.get("sae", {}).get("reward_divisor", 2.0))
        projectile_system = ProjectileSystem(
            pyramid_by_team={1: int(self.player_pyramid_eid), 2: int(self.enemy_pyramid_eid)},
            reward_divisor=reward_divisor
        )
        
        cleanup_system = CleanupSystem(protected_entities=pyramid_ids)
        
        # Enemy systems
        enemy_spawner_system = EnemySpawnerSystem(
            self.factory,
            self.balance,
            self.player_pyramid_eid,
            self.enemy_pyramid_eid,
            self.nav_grid,
            lanes_y=self.lanes_y,
        )
        
        # Note: DifficultySystem needs enemy_spawner but has compatibility issues
        # We'll add it later if needed
        difficulty_system = None
        
        # Register systems with priorities
        self.world.add_system(input_system, priority=10)
        self.world.add_system(economy_system, priority=15)
        self.world.add_system(upgrade_system, priority=18)
        self.world.add_system(enemy_spawner_system, priority=21)
        self.world.add_system(astar_system, priority=20)
        self.world.add_system(lane_route_system, priority=23)
        self.world.add_system(terrain_system, priority=25)
        self.world.add_system(nav_system, priority=30)
        self.world.add_system(targeting_system, priority=40)
        self.world.add_system(combat_system, priority=50)
        self.world.add_system(projectile_system, priority=60)
        self.world.add_system(cleanup_system, priority=90)
        
        # Store system references
        self.systems = {
            "input": input_system,
            "economy": economy_system,
            "upgrade": upgrade_system,
            "astar": astar_system,
            "terrain": terrain_system,
            "nav": nav_system,
            "targeting": targeting_system,
            "combat": combat_system,
            "projectile": projectile_system,
            "cleanup": cleanup_system,
            "lane_route": lane_route_system,
            "enemy_spawner": enemy_spawner_system,
            "difficulty": difficulty_system,
        }
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_attack_cell(self, team_id: int, lane_idx: int) -> tuple[int, int]:
        """
        Get the attack cell position for a given team and lane.
        
        Lane 1 (top): attacks from above
        Lane 2 (middle): attacks from side
        Lane 3 (bottom): attacks from below
        """
        w = self.nav_grid.width
        h = self.nav_grid.height
        px, py = int(self.player_pyr_pos[0]), int(self.player_pyr_pos[1])
        ex, ey = int(self.enemy_pyr_pos[0]), int(self.enemy_pyr_pos[1])
        
        if team_id == 1:  # Player attacks enemy
            if lane_idx == 0:
                ax, ay = ex, ey - 1
            elif lane_idx == 1:
                ax, ay = ex - 1, ey
            else:
                ax, ay = ex, ey + 1
        else:  # Enemy attacks player
            if lane_idx == 0:
                ax, ay = px, py - 1
            elif lane_idx == 1:
                ax, ay = px + 1, py
            else:
                ax, ay = px, py + 1
        
        return (self._clamp(ax, 1, w - 2), self._clamp(ay, 1, h - 2))
    
    def _find_walkable_near(self, x: int, y: int, max_r: int = 12) -> tuple[int, int]:
        """Find nearest walkable cell to (x, y)."""
        w = self.nav_grid.width
        h = self.nav_grid.height
        
        for r in range(0, max_r + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        if self.nav_grid.is_walkable(nx, ny):
                            return (nx, ny)
        return (x, y)
    
    def _force_open_cell(self, x: int, y: int, mult: float = 1.0):
        """Force a cell to be walkable."""
        self.nav_grid.set_cell(int(x), int(y), walkable=True, mult=float(mult))
    
    def _clamp(self, v: int, lo: int, hi: int) -> int:
        """Clamp value between lo and hi."""
        return lo if v < lo else hi if v > hi else v
    
    def _cell_cost(self, x: int, y: int) -> float:
        """Get movement cost for a cell (for A*)."""
        try:
            m = float(self.nav_grid.mult[y][x])
        except Exception:
            m = 1.0
        if m <= 0.0:
            return 999999.0
        return 1.0 / max(0.05, m)
    
    def _astar(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        """Run A* pathfinding between two points."""
        if start == goal:
            return [start]
        
        w = self.nav_grid.width
        h = self.nav_grid.height
        if w <= 0 or h <= 0:
            return []
        
        sx, sy = start
        gx, gy = goal
        if not self.nav_grid.is_walkable(sx, sy) or not self.nav_grid.is_walkable(gx, gy):
            return []
        
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        open_heap = [(0.0, 0.0, start)]
        came = {}
        gscore = {start: 0.0}
        closed = set()
        
        while open_heap:
            _f, g, cur = heapq.heappop(open_heap)
            if cur in closed:
                continue
            
            if cur == goal:
                path = [cur]
                while cur in came:
                    cur = came[cur]
                    path.append(cur)
                path.reverse()
                return path
            
            closed.add(cur)
            cx, cy = cur
            
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
                    continue
                if not self.nav_grid.is_walkable(nx, ny):
                    continue
                
                ng = g + self._cell_cost(nx, ny)
                if (nx, ny) not in gscore or ng < gscore[(nx, ny)]:
                    gscore[(nx, ny)] = ng
                    came[(nx, ny)] = cur
                    nf = ng + heuristic((nx, ny), goal)
                    heapq.heappush(open_heap, (nf, ng, (nx, ny)))
        
        return []
    
    def _compute_lane_route_path(self, lane_idx: int) -> list[tuple[int, int]]:
        """Compute the full path for a lane."""
        if not self.nav_grid:
            return []
        
        lane_idx = max(0, min(2, int(lane_idx)))
        lane_y = int(self.lanes_y[lane_idx])
        
        px, py = int(self.player_pyr_pos[0]), int(self.player_pyr_pos[1])
        ex = int(self.enemy_pyr_pos[0])
        
        h = self.nav_grid.height
        w = self.nav_grid.width
        
        # Start anchor (adjacent to pyramid based on lane)
        if lane_idx == 0:
            start_raw = (px, py - 1)  # Top
        elif lane_idx == 1:
            start_raw = (px + 1, py)  # Right
        else:
            start_raw = (px, py + 1)  # Bottom
        
        start_raw = (self._clamp(start_raw[0], 1, w - 2), self._clamp(start_raw[1], 1, h - 2))
        
        # Lane entry point
        entry_raw = (self._clamp(px + 1, 1, w - 2), lane_y)
        
        # Mid point near enemy
        mid_raw = (self._clamp(ex - 1, 1, w - 2), lane_y)
        
        # Attack cell
        end_raw = self.get_attack_cell(1, lane_idx)
        
        # Find walkable positions
        s = self._find_walkable_near(*start_raw)
        e = self._find_walkable_near(*entry_raw)
        m = self._find_walkable_near(*mid_raw)
        g = self._find_walkable_near(*end_raw)
        
        if not all([s, e, m, g]):
            return []
        
        # Build path in segments
        p1 = self._astar(s, e)
        p2 = self._astar(e, m)
        p3 = self._astar(m, g)
        
        out = []
        if p1:
            out += p1
        if p2:
            out += p2[1:] if out else p2
        if p3:
            out += p3[1:] if out else p3
        
        if out and tuple(out[0]) != tuple(start_raw):
            out.insert(0, start_raw)
        
        return out if out else [start_raw]
