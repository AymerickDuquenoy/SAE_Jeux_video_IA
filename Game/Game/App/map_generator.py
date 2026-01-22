# Game/App/map_generator.py
"""
Map generation utilities for Antique War.
Handles TMX file generation for random maps.
"""

import random
import xml.etree.ElementTree as ET
from pathlib import Path


def generate_tmx_map(
    output_path: Path,
    *,
    seed: int,
    width: int,
    height: int,
    tilewidth: int,
    tileheight: int,
    sand_tileset_source: str = "sable.tsx",
    quicksand_tileset_source: str = "sable_mouvant.tsx",
    sand_firstgid: int = 1,
    sand_tilecount: int = 24,
    quicksand_firstgid: int = 25,
    quicksand_tile_id: int = 20,  # => gid 45 (25+20)
    quicksand_rects: int = 7,
) -> None:
    """
    Generate a random TMX map file.
    
    Creates a visual map with:
    - Sand tiles: gid in [1..24] (visual variations)
    - Quicksand tiles: gid = 25 + 20 = 45 (from sable_mouvant.tsx)
    
    Note: This is purely visual. The actual navigation grid is handled
    separately by terrain_randomizer.apply_random_terrain().
    
    Args:
        output_path: Path to write the TMX file
        seed: Random seed for reproducibility
        width: Map width in tiles
        height: Map height in tiles
        tilewidth: Tile width in pixels
        tileheight: Tile height in pixels
        sand_tileset_source: Filename for sand tileset
        quicksand_tileset_source: Filename for quicksand tileset
        sand_firstgid: First GID for sand tiles
        sand_tilecount: Number of sand tile variations
        quicksand_firstgid: First GID for quicksand tiles
        quicksand_tile_id: Tile ID within quicksand tileset
        quicksand_rects: Number of quicksand patches to generate
    """
    rng = random.Random(seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    quick_gid = int(quicksand_firstgid + quicksand_tile_id)
    
    # Initialize grid with random sand tiles
    grid = []
    for _y in range(height):
        row = []
        for _x in range(width):
            row.append(rng.randint(sand_firstgid, sand_firstgid + sand_tilecount - 1))
        grid.append(row)
    
    # Add quicksand patches
    for _ in range(int(quicksand_rects)):
        rw = rng.randint(3, 8)
        rh = rng.randint(2, 5)
        x0 = rng.randint(1, max(1, width - 2 - rw))
        y0 = rng.randint(1, max(1, height - 2 - rh))
        
        for yy in range(y0, min(height - 1, y0 + rh)):
            for xx in range(x0, min(width - 1, x0 + rw)):
                grid[yy][xx] = quick_gid
    
    # Generate CSV data (pytmx compatible format)
    row_lines = []
    for row in grid:
        row_lines.append(",".join(str(v) for v in row))
    
    # Important: comma between rows for CSV format
    csv_text = ",\n".join(row_lines)
    
    # Build XML TMX structure
    root = ET.Element(
        "map",
        {
            "version": "1.10",
            "tiledversion": "1.11.2",
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "width": str(width),
            "height": str(height),
            "tilewidth": str(tilewidth),
            "tileheight": str(tileheight),
            "infinite": "0",
            "nextlayerid": "2",
            "nextobjectid": "1",
        },
    )
    
    # Add tileset references
    ET.SubElement(root, "tileset", {
        "firstgid": str(sand_firstgid),
        "source": sand_tileset_source
    })
    ET.SubElement(root, "tileset", {
        "firstgid": str(quicksand_firstgid),
        "source": quicksand_tileset_source
    })
    
    # Add tile layer
    layer = ET.SubElement(
        root,
        "layer",
        {
            "id": "1",
            "name": "Calque de Tuiles 1",
            "width": str(width),
            "height": str(height)
        },
    )
    data = ET.SubElement(layer, "data", {"encoding": "csv"})
    data.text = "\n" + csv_text + "\n"
    
    # Write to file
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def get_default_map_config(balance: dict) -> dict:
    """
    Extract map configuration from balance config.
    
    Args:
        balance: Balance configuration dictionary
        
    Returns:
        Dictionary with map configuration values
    """
    mp = balance.get("map", {})
    
    return {
        "width": int(mp.get("width", 30)),
        "height": int(mp.get("height", 20)),
        "tilewidth": int(mp.get("tilewidth", 32)),
        "tileheight": int(mp.get("tileheight", 32)),
        "dusty_rects": int(mp.get("dusty_rects", 7)),
        "forbidden_rects": int(mp.get("forbidden_rects", 3)),
        "player_pyramid": tuple(mp.get("player_pyramid", [2, 10])),
        "enemy_pyramid": tuple(mp.get("enemy_pyramid", [27, 10])),
        "player_spawn": tuple(mp.get("player_spawn", [3, 10])),
        "enemy_spawn": tuple(mp.get("enemy_spawn", [26, 10])),
    }
