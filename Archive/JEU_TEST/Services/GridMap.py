# GridMap.py
import pygame
import pytmx
from GridTile import GridTile


class GridMap:
    """Charge et affiche une carte Tiled (.tmx) avec les terrains et obstacles."""

    def __init__(self, filename: str):
        self.tmx_data = pytmx.util_pygame.load_pygame(filename)
        self.tilewidth = self.tmx_data.tilewidth
        self.tileheight = self.tmx_data.tileheight
        self.width = self.tmx_data.width
        self.height = self.tmx_data.height

        self.tiles = []
        self.load_tiles()

    def load_tiles(self):
        """Lit chaque tuile et récupère son type défini dans Tiled."""
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    image = self.tmx_data.get_tile_image_by_gid(gid)
                    if image:
                        props = self.tmx_data.get_tile_properties_by_gid(gid) or {}
                        terrain_type = props.get("type", "desert")  # <- propriété définie dans Tiled
                        tile = GridTile(image, x, y, terrain_type)
                        self.tiles.append(tile)

    def draw(self, surface, camera_x=0, camera_y=0):
        """Dessine toutes les tuiles visibles à l’écran."""
        for tile in self.tiles:
            tile.draw(surface, self.tilewidth, self.tileheight, camera_x, camera_y)


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    import sys

    pygame.init()

    # ⚠️ Fenêtre d'abord, sinon pytmx plante
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Carte Tiled avec terrains et obstacles")

    # 🔹 Charge la carte
    map_file = "Game/assets/map/map.tmx"
    game_map = GridMap(map_file)

    clock = pygame.time.Clock()
    camera_x = camera_y = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Déplacement caméra
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:  camera_x -= 5
        if keys[pygame.K_RIGHT]: camera_x += 5
        if keys[pygame.K_UP]:    camera_y -= 5
        if keys[pygame.K_DOWN]:  camera_y += 5

        screen.fill((0, 0, 0))
        game_map.draw(screen, camera_x, camera_y)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()
