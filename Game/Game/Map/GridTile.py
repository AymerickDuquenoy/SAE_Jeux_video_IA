# GridTile.py
import pygame

class GridTile:
    """
    Représente une tuile du terrain avec ses règles de gameplay.
    """

    VITESSE_MAX = 10
    VITESSE_ZERO = 0

    # Crée une tuile avec image, position et type de terrain
    def __init__(self, image: pygame.Surface, x: int, y: int, terrain_type: str = "desert"):
        self.image = image
        self.x = x
        self.y = y
        self.terrain_type = terrain_type.lower().strip()
        self.walkable = True
        self.speed = GridTile.VITESSE_MAX
        self._apply_terrain_rules()

    # Applique les règles de vitesse et traversabilité selon le type de terrain
    def _apply_terrain_rules(self):
        """Applique les vitesses et la traversabilité selon le type."""
        if self.terrain_type in ["desert"]:
            self.walkable = True
            self.speed = GridTile.VITESSE_MAX

        elif self.terrain_type in ["sables_mouvants", "sables mouvants", "quicksand"]:
            self.walkable = True
            self.speed = GridTile.VITESSE_MAX / 2

        elif self.terrain_type in ["pyramide", "camp", "camp ennemi"]:
            self.walkable = False
            self.speed = GridTile.VITESSE_ZERO

        elif self.terrain_type in ["cactus", "palmier", "palm tree"]:
            self.walkable = False
            self.speed = GridTile.VITESSE_ZERO

        else:
            # Par défaut, franchissable et vitesse max
            self.walkable = True
            self.speed = GridTile.VITESSE_MAX

    # Affiche la tuile sur la surface avec offset caméra
    def draw(self, surface, tile_width, tile_height, camera_x=0, camera_y=0):
        """Affiche la tuile sur la surface cible."""
        if self.image:
            surface.blit(
                self.image,
                (
                    self.x * tile_width - camera_x,
                    self.y * tile_height - camera_y
                )
            )

    # Retourne une représentation textuelle de la tuile
    def __repr__(self):
        return f"<Tile ({self.x},{self.y}) type={self.terrain_type} walkable={self.walkable} speed={self.speed}>"