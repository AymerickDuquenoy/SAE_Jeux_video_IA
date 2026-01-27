# Game/App/utils/grid_utils.py
"""Grid navigation utilities for Antique War."""

from Game.Map.NavigationGrid import NavigationGrid
from Game.Map.GridTile import GridTile


class GridUtils:
    """Utilitaires de manipulation de la grille de navigation."""

    def __init__(self, app):
        self.app = app

    def build_nav_from_map(self) -> NavigationGrid:
        """Construit une grille de navigation depuis la carte."""
        nav = NavigationGrid(int(self.app.game_map.width), int(self.app.game_map.height))
        vmax = float(getattr(GridTile, "VITESSE_MAX", 10.0))

        for t in getattr(self.app.game_map, "tiles", []):
            speed = float(getattr(t, "speed", vmax))
            walkable = bool(getattr(t, "walkable", True))
            mult = 0.0 if speed <= 0 else max(0.0, min(1.0, speed / vmax))
            nav.set_cell(int(t.x), int(t.y), walkable=walkable, mult=mult)

        # Bordure interdite (zone vitesse=0)
        w = int(getattr(nav, "width", 0))
        h = int(getattr(nav, "height", 0))
        if w > 0 and h > 0:
            for x in range(w):
                nav.set_cell(x, 0, walkable=False, mult=0.0)
                nav.set_cell(x, h - 1, walkable=False, mult=0.0)
            for y in range(h):
                nav.set_cell(0, y, walkable=False, mult=0.0)
                nav.set_cell(w - 1, y, walkable=False, mult=0.0)

        return nav

    def find_walkable_near(self, x: int, y: int, max_r: int = 10):
        """Trouve une case walkable proche de (x, y)."""
        w = int(getattr(self.app.nav_grid, "width", 0))
        h = int(getattr(self.app.nav_grid, "height", 0))
        for r in range(0, max_r + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        if self.app.nav_grid.is_walkable(nx, ny):
                            return nx, ny
        return None

    def force_open_cell(self, x: int, y: int, mult: float = 1.0):
        """Force une case à être walkable/open."""
        try:
            self.app.nav_grid.set_cell(int(x), int(y), walkable=True, mult=float(mult))
            return
        except Exception:
            pass

        # Fallback
        try:
            self.app.nav_grid.walkable[int(y)][int(x)] = True
        except Exception:
            pass
        try:
            self.app.nav_grid.mult[int(y)][int(x)] = float(mult)
        except Exception:
            pass

    def attack_cell_for_lane(self, team_id: int, lane_idx: int) -> tuple[int, int]:
        """
        Case d'attaque alignée avec la lane.
        Utilise lanes_y pour garantir l'alignement correct.
        """
        w = int(getattr(self.app.nav_grid, "width", 0))
        h = int(getattr(self.app.nav_grid, "height", 0))
        px, py = int(self.app.player_pyr_pos[0]), int(self.app.player_pyr_pos[1])
        ex, ey = int(self.app.enemy_pyr_pos[0]), int(self.app.enemy_pyr_pos[1])
        
        lane_y = int(self.app.lanes_y[lane_idx])

        if team_id == 1:
            # Joueur attaque pyramide ennemie
            if lane_idx == 1:
                ax, ay = ex - 1, lane_y
            else:
                ax, ay = ex, lane_y
        else:
            # Ennemi attaque pyramide joueur
            if lane_idx == 1:
                ax, ay = px + 1, lane_y
            else:
                ax, ay = px, lane_y

        ax = max(1, min(w - 2, int(ax)))
        ay = max(1, min(h - 2, int(ay)))
        return (ax, ay)

    def carve_pyramid_connectors(self):
        """
        Assure que les 3 lanes peuvent rejoindre des cases d'attaque différentes.
        - lane1 : haut
        - lane2 : milieu
        - lane3 : bas
        """
        if not self.app.nav_grid:
            return

        w = int(getattr(self.app.nav_grid, "width", 0))
        h = int(getattr(self.app.nav_grid, "height", 0))
        if w <= 0 or h <= 0:
            return

        px, py = int(self.app.player_pyr_pos[0]), int(self.app.player_pyr_pos[1])
        ex, ey = int(self.app.enemy_pyr_pos[0]), int(self.app.enemy_pyr_pos[1])

        # Colonnes "couloir"
        col_player = max(1, min(w - 2, px + 1))
        col_enemy = max(1, min(w - 2, ex - 1))

        ymin = max(1, min(self.app.lanes_y + [py, ey]))
        ymax = min(h - 2, max(self.app.lanes_y + [py, ey]))

        # Couloir vertical près des pyramides
        for y in range(ymin, ymax + 1):
            self.force_open_cell(col_player, y, 1.0)
            self.force_open_cell(col_enemy, y, 1.0)

        # Entrées lanes
        for ly in self.app.lanes_y:
            self.force_open_cell(col_player, int(ly), 1.0)
            self.force_open_cell(col_enemy, int(ly), 1.0)

        # Cases d'attaque lane (haut/milieu/bas)
        for lane_idx in (0, 1, 2):
            ax1, ay1 = self.attack_cell_for_lane(1, lane_idx)
            ax2, ay2 = self.attack_cell_for_lane(2, lane_idx)
            self.force_open_cell(ax1, ay1, 1.0)
            self.force_open_cell(ax2, ay2, 1.0)

        # Pad autour pyramides (anti blocage)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            x1 = max(1, min(w - 2, px + dx))
            y1 = max(1, min(h - 2, py + dy))
            self.force_open_cell(x1, y1, 1.0)

            x2 = max(1, min(w - 2, ex + dx))
            y2 = max(1, min(h - 2, ey + dy))
            self.force_open_cell(x2, y2, 1.0)

        # Mini-connecteurs autour de la pyramide ennemie
        for (xx, yy) in (
            (ex - 1, ey - 1),
            (ex - 1, ey + 1),
            (ex, ey - 1),
            (ex, ey + 1),
        ):
            if 1 <= xx < w - 1 and 1 <= yy < h - 1:
                self.force_open_cell(xx, yy, 1.0)

        # Mini-connecteurs autour de la pyramide joueur
        for (xx, yy) in (
            (px + 1, py - 1),
            (px + 1, py + 1),
            (px, py - 1),
            (px, py + 1),
        ):
            if 1 <= xx < w - 1 and 1 <= yy < h - 1:
                self.force_open_cell(xx, yy, 1.0)
