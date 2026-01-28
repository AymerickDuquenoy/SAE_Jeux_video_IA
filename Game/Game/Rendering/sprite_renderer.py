"""
SpriteRenderer - Rendu des unités avec sprites PNG animés.

Chaque sprite contient 2 frames côte à côte pour l'animation de marche.
- Momie (S): momie.png / momie_r.png (600x435 -> 2 frames de 300x435)
- Dromadaire (M): dromadaire.png / dromadaire_b.png (840x405 -> 2 frames de 420x405)
- Sphinx (L): sphinx.png / sphinx_b.png (1800x720 -> 2 frames de 900x720)
"""
import pygame
import os
import time


class SpriteRenderer:
    """Gère le rendu des sprites animés du jeu."""
    
    # Initialise le renderer de sprites avec cache et paramètres d'animation
    def __init__(self):
        self.cache = {}  # Cache des frames redimensionnées
        self.sprites_loaded = False
        self.frames = {}  # Stocke les 2 frames de chaque sprite
        self.pyramid_sprites = {}  # Stocke les sprites des pyramides par level et team
        
        # Tailles d'affichage des sprites
        self.momie_size = 28
        self.dromadaire_size = 36
        self.sphinx_size = 48
        
        # Tailles des pyramides par niveau (agrandissent avec le niveau)
        self.pyramid_sizes = {
            1: 45,
            2: 55,
            3: 70,
            4: 85,
            5: 100
        }
        
        # Vitesse d'animation (secondes par frame)
        self.anim_speed = 0.25
    
    # Retourne le chemin complet vers un fichier sprite
    def _get_sprite_path(self, filename: str) -> str:
        """Retourne le chemin complet vers un sprite."""
        base_paths = [
            os.path.join(os.path.dirname(__file__), "..", "assets", "sprites"),
            os.path.join(os.path.dirname(__file__), "assets", "sprites"),
            "Game/assets/sprites",
            "assets/sprites",
        ]
        for base in base_paths:
            path = os.path.join(base, filename)
            if os.path.exists(path):
                return path
        return None
    
    # Charge et découpe tous les sprites en frames
    def _load_sprites(self):
        """Charge et découpe tous les sprites en frames."""
        if self.sprites_loaded:
            return
        
        # Sprites des unités (2 frames chacun)
        sprite_files = {
            "momie_1": "momie.png",
            "momie_2": "momie_r.png",
            "dromadaire_1": "dromadaire.png",
            "dromadaire_2": "dromadaire_b.png",
            "sphinx_1": "sphinx.png",
            "sphinx_2": "sphinx_b.png",
        }
        
        for key, filename in sprite_files.items():
            path = self._get_sprite_path(filename)
            if path:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    w, h = img.get_size()
                    frame_w = w // 2
                    
                    # Découper en 2 frames
                    frame1 = img.subsurface((0, 0, frame_w, h))
                    frame2 = img.subsurface((frame_w, 0, frame_w, h))
                    
                    self.frames[key] = [frame1, frame2]
                except Exception as e:
                    print(f"[WARN] Could not load sprite {filename}: {e}")
                    self.frames[key] = None
            else:
                self.frames[key] = None
        
        # Sprites des pyramides (5 niveaux × 2 équipes)
        for level in range(1, 6):
            for team_id, team_name in [(1, "player"), (2, "enemy")]:
                filename = f"pyramid_{team_name}_{level}.png"
                path = self._get_sprite_path(filename)
                key = f"pyramid_{team_id}_{level}"
                
                if path:
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.pyramid_sprites[key] = img
                        print(f"[OK] Loaded {filename}")
                    except Exception as e:
                        print(f"[WARN] Could not load pyramid sprite {filename}: {e}")
                        self.pyramid_sprites[key] = None
                else:
                    self.pyramid_sprites[key] = None
        
        self.sprites_loaded = True
    
    # Retourne l'index de frame actuel (0 ou 1) pour l'animation
    def _get_current_frame_index(self) -> int:
        """Retourne l'index de frame actuel (0 ou 1) basé sur le temps."""
        return int(time.time() / self.anim_speed) % 2
    
    # Retourne une frame redimensionnée avec mise en cache
    def _get_scaled_frame(self, key: str, size: int, frame_idx: int) -> pygame.Surface:
        """Retourne une frame redimensionnée (avec cache)."""
        cache_key = f"{key}_{size}_{frame_idx}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        self._load_sprites()
        
        if key in self.frames and self.frames[key]:
            original = self.frames[key][frame_idx]
            # Garder le ratio
            orig_w, orig_h = original.get_size()
            ratio = min(size / orig_w, size / orig_h)
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
            if new_w > 0 and new_h > 0:
                scaled = pygame.transform.smoothscale(original, (new_w, new_h))
                self.cache[cache_key] = scaled
                return scaled
        
        return None
    
    # Dessine une momie animée avec sa barre de vie
    def draw_momie(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0, is_moving: bool = True):
        """Dessine une Momie animée (frame droite si à l'arrêt)."""
        key = f"momie_{team_id}"
        
        # Frame 1 (droite) si à l'arrêt, sinon animation
        if is_moving:
            frame_idx = self._get_current_frame_index()
        else:
            frame_idx = 1  # Frame de droite = arrêt
        
        sprite = self._get_scaled_frame(key, self.momie_size, frame_idx)
        
        if sprite:
            sw, sh = sprite.get_size()
            screen.blit(sprite, (x - sw // 2, y - sh // 2))
        else:
            # Fallback: cercle coloré
            color = (100, 180, 120) if team_id == 1 else (200, 100, 100)
            pygame.draw.circle(screen, color, (x, y), 7)
        
        self._draw_health_bar(screen, x, y - self.momie_size // 2 - 4, 18, hp_ratio, team_id)
    
    # Dessine un dromadaire animé avec sa barre de vie
    def draw_dromadaire(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0, is_moving: bool = True):
        """Dessine un Dromadaire animé (frame droite si à l'arrêt)."""
        key = f"dromadaire_{team_id}"
        
        # Frame 1 (droite) si à l'arrêt, sinon animation
        if is_moving:
            frame_idx = self._get_current_frame_index()
        else:
            frame_idx = 1  # Frame de droite = arrêt
        
        sprite = self._get_scaled_frame(key, self.dromadaire_size, frame_idx)
        
        if sprite:
            sw, sh = sprite.get_size()
            screen.blit(sprite, (x - sw // 2, y - sh // 2))
        else:
            # Fallback: cercle coloré
            color = (80, 180, 120) if team_id == 1 else (180, 80, 80)
            pygame.draw.circle(screen, color, (x, y), 10)
        
        self._draw_health_bar(screen, x, y - self.dromadaire_size // 2 - 4, 22, hp_ratio, team_id)
    
    # Dessine un sphinx animé avec sa barre de vie
    def draw_sphinx(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0, is_moving: bool = True):
        """Dessine un Sphinx animé (frame droite si à l'arrêt)."""
        key = f"sphinx_{team_id}"
        
        # Frame 1 (droite) si à l'arrêt, sinon animation
        if is_moving:
            frame_idx = self._get_current_frame_index()
        else:
            frame_idx = 1  # Frame de droite = arrêt
        
        sprite = self._get_scaled_frame(key, self.sphinx_size, frame_idx)
        
        if sprite:
            sw, sh = sprite.get_size()
            screen.blit(sprite, (x - sw // 2, y - sh // 2))
        else:
            # Fallback: cercle coloré
            color = (60, 160, 100) if team_id == 1 else (180, 60, 60)
            pygame.draw.circle(screen, color, (x, y), 13)
        
        self._draw_health_bar(screen, x, y - self.sphinx_size // 2 - 4, 28, hp_ratio, team_id)
    
    # Dessine une pyramide avec sprite PNG selon niveau et équipe
    def draw_pyramid(self, screen: pygame.Surface, x: int, y: int, team_id: int, 
                     hp_ratio: float = 1.0, level: int = 1):
        """Dessine une Pyramide avec sprite PNG."""
        self._load_sprites()
        
        # Limiter le niveau entre 1 et 5
        level = max(1, min(5, level))
        
        # Taille d'affichage selon le niveau
        display_size = self.pyramid_sizes.get(level, 60)
        
        # Clé du sprite
        sprite_key = f"pyramid_{team_id}_{level}"
        cache_key = f"pyramid_scaled_{team_id}_{level}_{display_size}"
        
        # Vérifier si le sprite existe
        sprite = self.pyramid_sprites.get(sprite_key)
        
        if sprite:
            # Redimensionner et mettre en cache si nécessaire
            if cache_key not in self.cache:
                orig_w, orig_h = sprite.get_size()
                # Garder les proportions
                scale = display_size / max(orig_w, orig_h)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled = pygame.transform.smoothscale(sprite, (new_w, new_h))
                self.cache[cache_key] = scaled
            
            scaled_sprite = self.cache[cache_key]
            sw, sh = scaled_sprite.get_size()
            
            # Dessiner le sprite centré sur la position
            screen.blit(scaled_sprite, (x - sw // 2, y - sh // 2))
            
            # Barre de vie sous la pyramide
            bar_w = display_size
            bar_h = 6
            bar_x = x - bar_w // 2
            bar_y = y + sh // 2 + 5
            
            pygame.draw.rect(screen, (40, 40, 40), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
            
            hp_color = (80, 220, 140) if team_id == 1 else (240, 100, 100)
            pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        else:
            # Fallback: dessin procédural si sprite non trouvé
            self._draw_pyramid_fallback(screen, x, y, team_id, hp_ratio, level)
    
    # Dessine une pyramide procédurale si sprite manquant (fallback)
    def _draw_pyramid_fallback(self, screen: pygame.Surface, x: int, y: int, 
                                team_id: int, hp_ratio: float, level: int):
        """Dessine une pyramide procédurale (fallback si sprite manquant)."""
        base_size = 28
        size = base_size + level * 6
        key = f"pyramid_fallback_l{level}_{team_id}_{size}"
        
        if key not in self.cache:
            surf = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
            
            if team_id == 1:
                color1 = (220, 180, 80)   # Doré joueur
                color2 = (180, 140, 60)
            else:
                color1 = (200, 90, 70)    # Rouge ennemi
                color2 = (160, 70, 50)
            
            cx, cy = (size + 4) // 2, (size + 4) // 2
            
            # Triangle principal
            points = [
                (cx, cy - size // 2),
                (cx - size // 2, cy + size // 3),
                (cx + size // 2, cy + size // 3)
            ]
            pygame.draw.polygon(surf, color1, points)
            pygame.draw.polygon(surf, color2, [points[0], points[2], (cx, cy)])
            pygame.draw.polygon(surf, (40, 40, 40), points, 2)
            
            self.cache[key] = surf
        
        screen.blit(self.cache[key], (x - (size + 4) // 2, y - (size + 4) // 2))
        
        # Barre de vie
        bar_w = size
        bar_h = 5
        bar_x = x - bar_w // 2
        bar_y = y + size // 3 + 10
        
        pygame.draw.rect(screen, (40, 40, 40), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        
        hp_color = (80, 220, 140) if team_id == 1 else (240, 100, 100)
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
    
    # Dessine un projectile coloré selon l'équipe
    def draw_projectile(self, screen: pygame.Surface, x: int, y: int, team_id: int):
        """Dessine un projectile."""
        if team_id == 1:
            color = (150, 255, 180)
        else:
            color = (255, 150, 150)
        
        pygame.draw.circle(screen, color, (x, y), 4)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), 2)
    
    # Dessine une barre de vie au-dessus d'une entité
    def _draw_health_bar(self, screen: pygame.Surface, x: int, y: int, 
                         width: int, ratio: float, team_id: int):
        """Dessine une barre de vie."""
        if ratio >= 1.0:
            return  # Pas besoin si pleine vie
            
        bar_h = 3
        bar_x = x - width // 2
        
        # Fond
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, y, width, bar_h))
        
        # Vie
        hp_color = (80, 220, 140) if team_id == 1 else (240, 120, 120)
        if ratio < 0.3:
            hp_color = (255, 100, 100)  # Rouge si critique
        
        pygame.draw.rect(screen, hp_color, (bar_x, y, int(width * ratio), bar_h))


# Instance globale
sprite_renderer = SpriteRenderer()