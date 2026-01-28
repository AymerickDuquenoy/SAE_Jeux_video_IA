# GridMap.py
import pytmx
from .GridTile import GridTile
from .NavigationGrid import NavigationGrid


class GridMap:
    """Charge et affiche une carte Tiled (.tmx) avec les terrains et obstacles."""

    # Charge une carte TMX avec pytmx et initialise les dimensions
    def __init__(self, filename: str):
        self.tmx_data = pytmx.util_pygame.load_pygame(filename)
        self.tilewidth = self.tmx_data.tilewidth
        self.tileheight = self.tmx_data.tileheight
        self.width = self.tmx_data.width
        self.height = self.tmx_data.height

        self.tiles = []
        self.tile_by_pos = {}
        self.load_tiles()

    # Détermine le type de terrain depuis les propriétés Tiled
    def _terrain_type_from_props(self, props: dict) -> str:
        """
        Tiled peut stocker le type de terrain de plusieurs façons.
        Dans ton projet actuel, les .tsx mettent des propriétés comme:
          - desert=""
          - sables_mouvants=""
        Donc on détecte:
          1) props["type"] si présent
          2) sinon, si une clé connue est présente, on prend son nom
          3) sinon "desert"
        """
        if not props:
            return "desert"

        t = props.get("type")
        if isinstance(t, str) and t.strip():
            return t.strip()

        # cas: propriétés sous forme de flags: desert="", sables_mouvants=""
        known = [
            "desert",
            "sables_mouvants",
            "sables mouvants",
            "quicksand",
            "cactus",
            "palmier",
            "palm tree",
            "pyramide",
            "camp",
            "camp ennemi",
        ]
        for k in known:
            if k in props:
                return k

        return "desert"

    # Lit toutes les tuiles de la carte et stocke leurs propriétés
    def load_tiles(self):
        """Lit chaque tuile et récupère son type défini dans Tiled."""
        self.tiles = []
        self.tile_by_pos = {}

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    image = self.tmx_data.get_tile_image_by_gid(gid)
                    # gid=0 => pas de tuile (on ne l'ajoute pas)
                    if image:
                        props = self.tmx_data.get_tile_properties_by_gid(gid) or {}
                        terrain_type = self._terrain_type_from_props(props)
                        tile = GridTile(image, x, y, terrain_type)

                        self.tiles.append(tile)
                        self.tile_by_pos[(x, y)] = tile

    # Retourne la tuile à une position donnée
    def get_tile(self, x: int, y: int):
        return self.tile_by_pos.get((x, y))

    # Convertit la carte en grille de navigation pour A*
    def to_navigation_grid(self) -> NavigationGrid:
        """
        Fabrique une NavigationGrid (pour A*) depuis la map.
        - open => mult=1
        - dusty => mult=1/n (ex: 0.5)
        - interdit => mult=0 et walkable=False
        """
        nav = NavigationGrid(self.width, self.height, default_walkable=False, default_mult=0.0)

        vmax = float(GridTile.VITESSE_MAX)

        for y in range(self.height):
            for x in range(self.width):
                tile = self.get_tile(x, y)

                # si aucune tuile, on considère bloqué (utile si tu mets des "vides" dans Tiled)
                if tile is None:
                    nav.set_cell(x, y, walkable=False, mult=0.0)
                    continue

                if not tile.walkable:
                    nav.set_cell(x, y, walkable=False, mult=0.0)
                else:
                    mult = float(tile.speed) / vmax if vmax > 0 else 1.0
                    nav.set_cell(x, y, walkable=True, mult=mult)

        return nav

    # Dessine toutes les tuiles visibles à l'écran avec offset caméra
    def draw(self, surface, camera_x=0, camera_y=0):
        """Dessine toutes les tuiles visibles à l’écran."""
        for tile in self.tiles:
            tile.draw(surface, self.tilewidth, self.tileheight, camera_x, camera_y)