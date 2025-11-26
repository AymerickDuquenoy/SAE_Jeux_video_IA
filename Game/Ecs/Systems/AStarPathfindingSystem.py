"""A* pathfinding utilities.

This module provides:
- `astar(grid_map, start, goal, allow_diagonal=False)` which dispatches based on
  the provided map: if `grid_map` has attribute `tiles` it is treated as the
  project's `GridMap` (uses `GridTile` attributes `walkable` and `speed`),
  otherwise if it's a 2D numpy array it will run A* on that array (0=free, 1=blocked).

The implementation for `GridMap` uses tile `speed` to weight movement cost (slower
tiles are more expensive). The numpy-grid implementation uses unit costs.
"""
from typing import List, Tuple, Dict, Optional, Sequence
import heapq
import math

Point = Tuple[int, int]


def _heuristic(a: Point, b: Point, diagonal: bool) -> float:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    if diagonal:
        # Octile distance
        F = math.sqrt(2) - 1
        return (dx + dy) + (F * min(dx, dy)) - min(dx, dy)
    return dx + dy


def _neighbors_4_8(pos: Point, width: Optional[int], height: Optional[int], diagonal: bool) -> List[Point]:
    x, y = pos
    nbrs = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    if diagonal:
        nbrs += [(x + 1, y + 1), (x + 1, y - 1), (x - 1, y + 1), (x - 1, y - 1)]
    if width is None or height is None:
        return nbrs
    out = []
    for nx, ny in nbrs:
        if 0 <= nx < width and 0 <= ny < height:
            out.append((nx, ny))
    return out


def astar_gridmap(grid_map, start: Point, goal: Point, allow_diagonal: bool = False) -> Optional[List[Point]]:
    """A* using `GridMap` / `GridTile` objects.

    - `grid_map` must expose `.tiles` iterable and optionally `.width` and `.height`.
    - Each tile must have `.x`, `.y`, `.walkable` and `.speed` attributes.
    - `start` and `goal` are `(x,y)` tile coordinates.
    """
    # Build lookup
    tile_map: Dict[Point, object] = {}
    for t in getattr(grid_map, "tiles", []):
        tile_map[(t.x, t.y)] = t

    # Determine max speed for scaling
    speeds = [getattr(t, "speed", 0) for t in tile_map.values() if getattr(t, "speed", 0) > 0]
    max_speed = max(speeds) if speeds else 1.0

    def cost(a: Point, b: Point) -> float:
        tile = tile_map.get(b)
        if tile is None or not getattr(tile, "walkable", True):
            return float("inf")
        s = float(getattr(tile, "speed", max_speed))
        base = 1.0
        if a[0] != b[0] and a[1] != b[1]:
            base *= math.sqrt(2)
        # slower tiles => higher cost
        return base * (max_speed / s)

    width = getattr(grid_map, "width", None)
    height = getattr(grid_map, "height", None)

    open_heap = []
    g_score: Dict[Point, float] = {start: 0.0}
    came_from: Dict[Point, Point] = {}
    f0 = _heuristic(start, goal, allow_diagonal)
    counter = 0
    heapq.heappush(open_heap, (f0, counter, start))
    closed = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            # reconstruct
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        closed.add(current)
        for nbr in _neighbors_4_8(current, width, height, allow_diagonal):
            if nbr in closed:
                continue
            tile = tile_map.get(nbr)
            if tile is None or not getattr(tile, "walkable", True):
                continue
            tentative = g_score.get(current, float("inf")) + cost(current, nbr)
            if tentative < g_score.get(nbr, float("inf")):
                came_from[nbr] = current
                g_score[nbr] = tentative
                f = tentative + _heuristic(nbr, goal, allow_diagonal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nbr))

    return None


def astar_numpy(grid, start: Point, goal: Point, allow_diagonal: bool = True) -> Optional[List[Point]]:
    """A* over a 2D numpy-like grid (indexable as grid[x,y]), where 0 = free, 1 = blocked.

    `start` and `goal` are (x,y) tuples.
    """
    try:
        import numpy as _np
    except Exception:
        _np = None

    # Support sequences of sequences too
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    def is_blocked(p: Point) -> bool:
        x, y = p
        return grid[x][y] != 0

    open_heap = []
    g_score: Dict[Point, float] = {start: 0.0}
    came_from: Dict[Point, Point] = {}
    f0 = _heuristic(start, goal, allow_diagonal)
    counter = 0
    heapq.heappush(open_heap, (f0, counter, start))
    closed = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        closed.add(current)
        for nbr in _neighbors_4_8(current, rows, cols, allow_diagonal):
            if nbr in closed:
                continue
            if is_blocked(nbr):
                continue
            # movement cost
            step_cost = math.sqrt(2) if (nbr[0] != current[0] and nbr[1] != current[1]) else 1.0
            tentative = g_score.get(current, float("inf")) + step_cost
            if tentative < g_score.get(nbr, float("inf")):
                came_from[nbr] = current
                g_score[nbr] = tentative
                f = tentative + _heuristic(nbr, goal, allow_diagonal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nbr))

    return None


def astar(grid_map_or_grid, start: Point, goal: Point, allow_diagonal: bool = False) -> Optional[List[Point]]:
    """Dispatching helper: accepts either a `GridMap` (has `.tiles`) or a 2D grid (list or numpy array).

    Returns list of (x,y) points or None when no path found.
    """
    # If object has tiles attribute -> GridMap
    if hasattr(grid_map_or_grid, "tiles"):
        return astar_gridmap(grid_map_or_grid, start, goal, allow_diagonal=allow_diagonal)

    # Otherwise treat as 2D grid
    return astar_numpy(grid_map_or_grid, start, goal, allow_diagonal=allow_diagonal)


if __name__ == "__main__":
    print("AStar module: use astar(grid_map_or_grid, start, goal, allow_diagonal=False)")
from typing import List, Tuple, Dict, Set
import numpy as np
import heapq
import matplotlib.pyplot as plt
from math import sqrt
def create_node(position: Tuple[int, int], g: float = float('inf'), 
                h: float = 0.0, parent: Dict = None) -> Dict:
    """
    Create a node for the A* algorithm.
    
    Args:
        position: (x, y) coordinates of the node
        g: Cost from start to this node (default: infinity)
        h: Estimated cost from this node to goal (default: 0)
        parent: Parent node (default: None)
    
    Returns:
        Dictionary containing node information
    """
    return {
        'position': position,
        'g': g,
        'h': h,
        'f': g + h,
        'parent': parent
    }
    
def calculate_heuristic(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """
    Calculate the estimated distance between two points using Euclidean distance.
    """
    x1, y1 = pos1
    x2, y2 = pos2
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)
def get_valid_neighbors(grid: np.ndarray, position: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Get all valid neighboring positions in the grid.
    
    Args:
        grid: 2D numpy array where 0 represents walkable cells and 1 represents obstacles
        position: Current position (x, y)
    
    Returns:
        List of valid neighboring positions
    """
    x, y = position
    rows, cols = grid.shape
    
    # All possible moves (including diagonals)
    possible_moves = [
        (x+1, y), (x-1, y),    # Right, Left
        (x, y+1), (x, y-1),    # Up, Down
        (x+1, y+1), (x-1, y-1),  # Diagonal moves
        (x+1, y-1), (x-1, y+1)
    ]
    
    return [
        (nx, ny) for nx, ny in possible_moves
        if 0 <= nx < rows and 0 <= ny < cols  # Within grid bounds
        and grid[nx, ny] == 0                # Not an obstacle
    ]
def reconstruct_path(goal_node: Dict) -> List[Tuple[int, int]]:
    """
    Reconstruct the path from goal to start by following parent pointers.
    """
    path = []
    current = goal_node
    
    while current is not None:
        path.append(current['position'])
        current = current['parent']
        
    return path[::-1]  # Reverse to get path from start to goal
def find_path(grid: np.ndarray, start: Tuple[int, int], 
              goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Find the optimal path using A* algorithm.
    
    Args:
        grid: 2D numpy array (0 = free space, 1 = obstacle)
        start: Starting position (x, y)
        goal: Goal position (x, y)
    
    Returns:
        List of positions representing the optimal path
    """
    # Initialize start node
    start_node = create_node(
        position=start,
        g=0,
        h=calculate_heuristic(start, goal)
    )
    
    # Initialize open and closed sets
    open_list = [(start_node['f'], start)]  # Priority queue
    open_dict = {start: start_node}         # For quick node lookup
    closed_set = set()                      # Explored nodes
    
    while open_list:
        # Get node with lowest f value
        _, current_pos = heapq.heappop(open_list)
        current_node = open_dict[current_pos]
        
        # Check if we've reached the goal
        if current_pos == goal:
            return reconstruct_path(current_node)
            
        closed_set.add(current_pos)
        
        # Explore neighbors
        for neighbor_pos in get_valid_neighbors(grid, current_pos):
            # Skip if already explored
            if neighbor_pos in closed_set:
                continue
                
            # Calculate new path cost
            tentative_g = current_node['g'] + calculate_heuristic(current_pos, neighbor_pos)
            
            # Create or update neighbor
            if neighbor_pos not in open_dict:
                neighbor = create_node(
                    position=neighbor_pos,
                    g=tentative_g,
                    h=calculate_heuristic(neighbor_pos, goal),
                    parent=current_node
                )
                heapq.heappush(open_list, (neighbor['f'], neighbor_pos))
                open_dict[neighbor_pos] = neighbor
            elif tentative_g < open_dict[neighbor_pos]['g']:
                # Found a better path to the neighbor
                neighbor = open_dict[neighbor_pos]
                neighbor['g'] = tentative_g
                neighbor['f'] = tentative_g + neighbor['h']
                neighbor['parent'] = current_node
    
    return []  # No path found






""" test code
def visualize_path(grid: np.ndarray, path: List[Tuple[int, int]]):
    plt.figure(figsize=(10, 10))
    plt.imshow(grid, cmap='binary')
    
    if path:
        path = np.array(path)
        plt.plot(path[:, 1], path[:, 0], 'b-', linewidth=3, label='Path')
        plt.plot(path[0, 1], path[0, 0], 'go', markersize=15, label='Start')
        plt.plot(path[-1, 1], path[-1, 0], 'ro', markersize=15, label='Goal')
    
    plt.grid(True)
    plt.legend(fontsize=12)
    plt.title("A* Pathfinding Result")
    plt.show()
    # Create a sample grid
grid = np.zeros((20, 20))  # 20x20 grid, all free space initially
# Add some obstacles
grid[5:15, 5] = 1  # Vertical wall
grid[5, 5:15] = 1   # Horizontal wall
# Define start and goal positions
start_pos = (0, 1)
goal_pos = (19, 18)
# Find the path
path = find_path(grid, start_pos, goal_pos)
if path:
    print(f"Path found with {len(path)} steps!")
    visualize_path(grid, path)
else:
    print("No path found!")"""