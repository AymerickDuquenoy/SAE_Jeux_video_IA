# Game/Services/tmx_generator.py
from __future__ import annotations

import random
from pathlib import Path
import xml.etree.ElementTree as ET


def _csv_data(grid: list[list[int]]) -> str:
    # Format proche de Tiled (une ligne par row, virgules, avec retour ligne)
    lines = []
    for row in grid:
        lines.append(",".join(str(v) for v in row) + ",")
    return "\n".join(lines)


def generate_random_tmx(
    output_path: Path,
    *,
    width: int,
    height: int,
    tilewidth: int = 32,
    tileheight: int = 32,
    rng: random.Random | None = None,
    # Tilesets de ton dossier assets/map
    sand_tileset_source: str = "sable.tsx",
    quicksand_tileset_source: str = "sable_mouvant.tsx",
    sand_firstgid: int = 1,
    sand_tilecount: int = 24,          # sable.tsx => tilecount=24
    quicksand_firstgid: int = 25,      # map.tmx => firstgid 25
    quicksand_tile_id: int = 20,       # sable_mouvant.tsx => tile id 20 a la property sables_mouvants
    # Génération
    quicksand_rects: int = 6,
    rect_w_range: tuple[int, int] = (3, 8),
    rect_h_range: tuple[int, int] = (2, 5),
) -> Path:
    """
    Génère un .tmx "visuel" aléatoire :
      - sable : gid dans [1..24] (variations visuelles du tileset sable)
      - sables mouvants : gid = firstgid(25) + tile_id(20) = 45
    On ne gère pas ici les zones interdites (ça reste côté NavigationGrid + apply_random_terrain).
    """

    if rng is None:
        rng = random.Random()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # gid quicksand (celui qui a la property "sables_mouvants")
    quick_gid = int(quicksand_firstgid + quicksand_tile_id)

    # 1) Base sable aléatoire (visuel différent à chaque run)
    grid = []
    for _y in range(height):
        row = []
        for _x in range(width):
            # sable tile gid : 1..24
            row.append(rng.randint(sand_firstgid, sand_firstgid + sand_tilecount - 1))
        grid.append(row)

    # 2) Patchs de sables mouvants (rectangles)
    for _ in range(int(quicksand_rects)):
        rw = rng.randint(rect_w_range[0], rect_w_range[1])
        rh = rng.randint(rect_h_range[0], rect_h_range[1])
        x0 = rng.randint(1, max(1, width - 2 - rw))
        y0 = rng.randint(1, max(1, height - 2 - rh))

        for yy in range(y0, min(height - 1, y0 + rh)):
            for xx in range(x0, min(width - 1, x0 + rw)):
                grid[yy][xx] = quick_gid

    # 3) XML TMX
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

    ET.SubElement(root, "tileset", {"firstgid": str(sand_firstgid), "source": sand_tileset_source})
    ET.SubElement(root, "tileset", {"firstgid": str(quicksand_firstgid), "source": quicksand_tileset_source})

    layer = ET.SubElement(root, "layer", {"id": "1", "name": "Calque de Tuiles 1", "width": str(width), "height": str(height)})
    data = ET.SubElement(layer, "data", {"encoding": "csv"})
    data.text = "\n" + _csv_data(grid) + "\n"

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    return output_path
