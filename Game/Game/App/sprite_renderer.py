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
    
    def __init__(self):
        self.cache = {}  # Cache des frames redimensionnées
        self.sprites_loaded = False
        self.frames = {}  # Stocke les 2 frames de chaque sprite
        
        # Tailles d'affichage des sprites
        self.momie_size = 28
        self.dromadaire_size = 36
        self.sphinx_size = 48
        
        # Vitesse d'animation (secondes par frame)
        self.anim_speed = 0.25
    
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
    
    def _load_sprites(self):
        """Charge et découpe tous les sprites en frames."""
        if self.sprites_loaded:
            return
        
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
        
        self.sprites_loaded = True
    
    def _get_current_frame_index(self) -> int:
        """Retourne l'index de frame actuel (0 ou 1) basé sur le temps."""
        return int(time.time() / self.anim_speed) % 2
    
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
    
    def draw_momie(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0):
        """Dessine une Momie animée."""
        key = f"momie_{team_id}"
        frame_idx = self._get_current_frame_index()
        sprite = self._get_scaled_frame(key, self.momie_size, frame_idx)
        
        if sprite:
            sw, sh = sprite.get_size()
            screen.blit(sprite, (x - sw // 2, y - sh // 2))
        else:
            # Fallback: cercle coloré
            color = (100, 180, 120) if team_id == 1 else (200, 100, 100)
            pygame.draw.circle(screen, color, (x, y), 7)
        
        self._draw_health_bar(screen, x, y - self.momie_size // 2 - 4, 18, hp_ratio, team_id)
    
    def draw_dromadaire(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0):
        """Dessine un Dromadaire animé."""
        key = f"dromadaire_{team_id}"
        frame_idx = self._get_current_frame_index()
        sprite = self._get_scaled_frame(key, self.dromadaire_size, frame_idx)
        
        if sprite:
            sw, sh = sprite.get_size()
            screen.blit(sprite, (x - sw // 2, y - sh // 2))
        else:
            # Fallback: cercle coloré
            color = (80, 180, 120) if team_id == 1 else (180, 80, 80)
            pygame.draw.circle(screen, color, (x, y), 10)
        
        self._draw_health_bar(screen, x, y - self.dromadaire_size // 2 - 4, 22, hp_ratio, team_id)
    
    def draw_sphinx(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0):
        """Dessine un Sphinx animé."""
        key = f"sphinx_{team_id}"
        frame_idx = self._get_current_frame_index()
        sprite = self._get_scaled_frame(key, self.sphinx_size, frame_idx)
        
        if sprite:
            sw, sh = sprite.get_size()
            screen.blit(sprite, (x - sw // 2, y - sh // 2))
        else:
            # Fallback: cercle coloré
            color = (60, 160, 100) if team_id == 1 else (180, 60, 60)
            pygame.draw.circle(screen, color, (x, y), 13)
        
        self._draw_health_bar(screen, x, y - self.sphinx_size // 2 - 4, 28, hp_ratio, team_id)
    
    def draw_pyramid(self, screen: pygame.Surface, x: int, y: int, team_id: int, 
                     hp_ratio: float = 1.0, level: int = 1):
        """Dessine une Pyramide (sprite procédural)."""
        base_size = 28
        size = base_size + level * 2
        key = f"pyramid_l{level}_{team_id}_{size}"
        
        if key not in self.cache:
            surf = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
            
            if team_id == 1:
                color1 = (80, 180, 120)   # Vert joueur
                color2 = (60, 140, 90)
            else:
                color1 = (200, 90, 90)    # Rouge ennemi
                color2 = (160, 70, 70)
            
            cx, cy = (size + 4) // 2, (size + 4) // 2
            
            # Triangle principal
            points = [
                (cx, cy - size // 2),
                (cx - size // 2, cy + size // 3),
                (cx + size // 2, cy + size // 3)
            ]
            pygame.draw.polygon(surf, color1, points)
            
            # Face ombrée
            shadow_points = [
                (cx, cy - size // 2),
                (cx + size // 2, cy + size // 3),
                (cx, cy + size // 3 - 5)
            ]
            pygame.draw.polygon(surf, color2, shadow_points)
            
            # Lignes de briques
            for i in range(1, level + 2):
                yy = cy - size // 2 + i * (size // (level + 3))
                half_w = (i * size // (level + 4))
                pygame.draw.line(surf, (40, 40, 40), 
                               (cx - half_w, yy), (cx + half_w, yy), 1)
            
            # Contour
            pygame.draw.polygon(surf, (40, 40, 40), points, 2)
            
            # Étoile niveau (si level > 1)
            if level > 1:
                for i in range(level - 1):
                    star_x = cx - (level - 2) * 4 + i * 8
                    pygame.draw.circle(surf, (255, 220, 100), (star_x, cy + size // 3 - 8), 2)
            
            self.cache[key] = surf
        
        screen.blit(self.cache[key], (x - (size + 4) // 2, y - (size + 4) // 2))
        
        # Barre de vie plus grande pour pyramide
        bar_w = size
        bar_h = 5
        bar_x = x - bar_w // 2
        bar_y = y - size // 2 - 10
        
        pygame.draw.rect(screen, (40, 40, 40), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        
        hp_color = (80, 220, 140) if team_id == 1 else (240, 100, 100)
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
    
    def draw_projectile(self, screen: pygame.Surface, x: int, y: int, team_id: int):
        """Dessine un projectile."""
        if team_id == 1:
            color = (150, 255, 180)
        else:
            color = (255, 150, 150)
        
        pygame.draw.circle(screen, color, (x, y), 4)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), 2)
    
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
