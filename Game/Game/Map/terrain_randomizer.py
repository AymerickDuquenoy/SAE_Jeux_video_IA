# Game/Services/terrain_randomizer.py
from __future__ import annotations

import random
from typing import Iterable, Tuple, Dict, Optional

from Game.Map.NavigationGrid import NavigationGrid

Pos = Tuple[int, int]

# Clamp une valeur entre lo et hi
def _clamp(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v

# Vérifie si une position est proche d'une liste de positions protégées
def _is_near_any(pos: Pos, protected: set[Pos], radius: int) -> bool:
    x, y = pos
    for px, py in protected:
        if abs(px - x) <= radius and abs(py - y) <= radius:
            return True
    return False

# Applique un terrain aléatoire sur une grille de navigation existante
def apply_random_terrain(
    nav: NavigationGrid,
    *,
    lanes_y: list[int],
    protected_positions: Iterable[Pos],
    rng: Optional[random.Random] = None,
    dusty_divisor: float = 2.0,       # Vmax / n  => mult = 1/n
    dusty_rects: int = 7,
    forbidden_rects: int = 3,
    corridor_half_height: int = 1,    # corridor “safe” autour des lanes (±1)
) -> Dict[str, int]:
    """
    Ajoute une couche de terrain aléatoire sur une nav grid existante.
    Zones SAÉ :
      - open : walkable True, mult = 1.0
      - dusty : walkable True, mult = 1/n
      - forbidden : walkable False, mult = 0.0

    IMPORTANT :
    - On garde les lanes jouables (pas de forbidden dans le corridor),
    - mais on autorise dusty dans le corridor pour que l'A* ait un vrai choix.
    """

    if rng is None:
        rng = random.Random()

    w = int(getattr(nav, "width", 0))
    h = int(getattr(nav, "height", 0))
    if w <= 2 or h <= 2:
        return {"open": 0, "dusty": 0, "forbidden": 0}

    protected = set((int(x), int(y)) for x, y in protected_positions)

    # 1) Corridors "safe" (walkable) autour des lanes
    # On force walkable=True + mult=1.0 ici, MAIS dusty pourra repasser derrière.
    for ly in lanes_y:
        ly = _clamp(int(ly), 1, h - 2)
        for dy in range(-corridor_half_height, corridor_half_height + 1):
            yy = _clamp(ly + dy, 1, h - 2)
            for x in range(1, w - 1):
                nav.set_cell(x, yy, walkable=True, mult=1.0)

    def _in_lane_corridor(y: int) -> bool:
        for ly in lanes_y:
            if abs(int(y) - int(ly)) <= corridor_half_height:
                return True
        return False

    def paint_rect(x0: int, y0: int, rw: int, rh: int, *, kind: str) -> bool:
        painted = False

        # On évite les rectangles FORBIDDEN trop proches des lanes (sinon ça casse la jouabilité).
        if kind == "forbidden":
            for ly in lanes_y:
                if abs(int(y0) - int(ly)) <= corridor_half_height:
                    return False

        for yy in range(y0, y0 + rh):
            for xx in range(x0, x0 + rw):
                if xx <= 0 or xx >= w - 1 or yy <= 0 or yy >= h - 1:
                    continue

                if _is_near_any((xx, yy), protected, radius=1):
                    continue

                # On interdit seulement le FORBIDDEN dans le corridor des lanes.
                if kind == "forbidden" and _in_lane_corridor(yy):
                    continue

                if kind == "dusty":
                    nav.set_cell(
                        xx,
                        yy,
                        walkable=True,
                        mult=(1.0 / max(1.0, float(dusty_divisor))),
                    )
                    painted = True
                elif kind == "forbidden":
                    nav.set_cell(xx, yy, walkable=False, mult=0.0)
                    painted = True

        return painted

    # 2) Dusty patches (autorisé aussi sur lanes => A* a un vrai choix)
    for _ in range(int(dusty_rects)):
        rw = rng.randint(3, 8)
        rh = rng.randint(2, 5)
        x0 = rng.randint(1, max(1, w - 1 - rw))
        y0 = rng.randint(1, max(1, h - 1 - rh))
        paint_rect(x0, y0, rw, rh, kind="dusty")

    # 3) Forbidden patches (jamais dans les lanes)
    for _ in range(int(forbidden_rects)):
        rw = rng.randint(2, 6)
        rh = rng.randint(2, 5)
        x0 = rng.randint(1, max(1, w - 1 - rw))
        y0 = rng.randint(1, max(1, h - 1 - rh))
        paint_rect(x0, y0, rw, rh, kind="forbidden")

    # 4) Comptage zones
    open_c = 0
    dusty_c = 0
    forb_c = 0
    for y in range(h):
        for x in range(w):
            walk = nav.is_walkable(x, y)
            m = float(nav.mult[y][x])
            if (not walk) or m <= 0.0:
                forb_c += 1
            elif m < 0.99:
                dusty_c += 1
            else:
                open_c += 1

    # 5) Force au moins 1 case dusty + 1 case forbidden (rare mais possible)
    if dusty_c == 0:
        cx = w // 2
        cy = _clamp(h // 3, 2, h - 3)
        nav.set_cell(cx, cy, walkable=True, mult=(1.0 / max(1.0, float(dusty_divisor))))
        dusty_c += 1

    if forb_c == 0:
        cx = w // 2
        cy = _clamp((2 * h) // 3, 2, h - 3)
        # évite corridor lane si par hasard
        if _in_lane_corridor(cy):
            cy = _clamp(cy + (corridor_half_height + 2), 2, h - 3)
        nav.set_cell(cx, cy, walkable=False, mult=0.0)
        forb_c += 1

    return {"open": open_c, "dusty": dusty_c, "forbidden": forb_c}
