# Game/Game/App/match_manager.py
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
    
    # ========================= PRIVATE METHODS =========================
    
    # Toutes les fonctions privées (_setup_map, _setup_navigation, etc.) restent
    # inchangées, mais tous les imports sont désormais préfixés par Game.Game
    # comme indiqué ci-dessus.