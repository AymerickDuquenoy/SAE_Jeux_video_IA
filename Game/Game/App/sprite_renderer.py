"""
SpriteRenderer - Rendu stylisé des unités et bâtiments.

Génère des sprites procéduraux pour chaque type d'entité :
- Momie (S): Silhouette bandée
- Dromadaire (M): Forme de chameau stylisée
- Sphinx (L): Sphinx égyptien majestueux
- Pyramide: Pyramide avec détails
"""
import pygame
import math


class SpriteRenderer:
    """Gère le rendu des sprites du jeu."""
    
    def __init__(self):
        self.cache = {}  # Cache des surfaces générées
        
    def _get_cache_key(self, sprite_type: str, team_id: int, size: int) -> str:
        return f"{sprite_type}_{team_id}_{size}"
    
    def draw_momie(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0):
        """Dessine une Momie (petite unité rapide)."""
        size = 14
        key = self._get_cache_key("momie", team_id, size)
        
        if key not in self.cache:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Couleurs selon équipe
            if team_id == 1:
                body_color = (200, 220, 180)  # Bandages beige
                accent = (100, 180, 120)      # Vert joueur
            else:
                body_color = (180, 180, 160)
                accent = (200, 100, 100)      # Rouge ennemi
            
            # Corps (ovale vertical)
            cx, cy = size // 2, size // 2
            pygame.draw.ellipse(surf, body_color, (cx - 4, cy - 6, 8, 12))
            
            # Bandages horizontaux
            for i in range(3):
                yy = cy - 4 + i * 3
                pygame.draw.line(surf, (150, 150, 130), (cx - 3, yy), (cx + 3, yy), 1)
            
            # Yeux brillants
            pygame.draw.circle(surf, accent, (cx - 2, cy - 3), 2)
            pygame.draw.circle(surf, accent, (cx + 2, cy - 3), 2)
            
            # Contour
            pygame.draw.ellipse(surf, (60, 60, 50), (cx - 4, cy - 6, 8, 12), 1)
            
            self.cache[key] = surf
        
        screen.blit(self.cache[key], (x - size // 2, y - size // 2))
        self._draw_health_bar(screen, x, y - 10, 12, hp_ratio, team_id)
    
    def draw_dromadaire(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0):
        """Dessine un Dromadaire (unité moyenne tank)."""
        size = 20
        key = self._get_cache_key("dromadaire", team_id, size)
        
        if key not in self.cache:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            
            if team_id == 1:
                body_color = (180, 150, 100)  # Chameau beige
                accent = (80, 180, 120)
            else:
                body_color = (160, 130, 90)
                accent = (180, 80, 80)
            
            cx, cy = size // 2, size // 2
            
            # Corps (ovale horizontal)
            pygame.draw.ellipse(surf, body_color, (cx - 7, cy - 3, 14, 8))
            
            # Bosse
            pygame.draw.ellipse(surf, body_color, (cx - 2, cy - 6, 6, 5))
            
            # Tête
            pygame.draw.circle(surf, body_color, (cx + 5, cy - 1), 3)
            
            # Œil
            pygame.draw.circle(surf, (40, 40, 40), (cx + 6, cy - 2), 1)
            
            # Pattes (lignes)
            pygame.draw.line(surf, (120, 100, 70), (cx - 4, cy + 4), (cx - 4, cy + 8), 2)
            pygame.draw.line(surf, (120, 100, 70), (cx + 3, cy + 4), (cx + 3, cy + 8), 2)
            
            # Contour coloré selon équipe
            pygame.draw.ellipse(surf, accent, (cx - 7, cy - 3, 14, 8), 2)
            
            self.cache[key] = surf
        
        screen.blit(self.cache[key], (x - size // 2, y - size // 2))
        self._draw_health_bar(screen, x, y - 14, 16, hp_ratio, team_id)
    
    def draw_sphinx(self, screen: pygame.Surface, x: int, y: int, team_id: int, hp_ratio: float = 1.0):
        """Dessine un Sphinx (grosse unité siège)."""
        size = 26
        key = self._get_cache_key("sphinx", team_id, size)
        
        if key not in self.cache:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            
            if team_id == 1:
                body_color = (220, 190, 120)  # Or
                accent = (60, 160, 100)
            else:
                body_color = (200, 170, 100)
                accent = (180, 60, 60)
            
            cx, cy = size // 2, size // 2
            
            # Corps du lion (rectangle arrondi)
            pygame.draw.rect(surf, body_color, (cx - 9, cy - 2, 16, 8), border_radius=3)
            
            # Tête humaine
            pygame.draw.circle(surf, body_color, (cx + 6, cy - 4), 5)
            
            # Coiffe égyptienne (triangle)
            points = [(cx + 6, cy - 9), (cx + 2, cy - 2), (cx + 10, cy - 2)]
            pygame.draw.polygon(surf, accent, points)
            
            # Pattes avant
            pygame.draw.rect(surf, body_color, (cx - 8, cy + 5, 4, 5))
            pygame.draw.rect(surf, body_color, (cx + 4, cy + 5, 4, 5))
            
            # Visage
            pygame.draw.circle(surf, (40, 40, 40), (cx + 5, cy - 5), 1)
            pygame.draw.circle(surf, (40, 40, 40), (cx + 8, cy - 5), 1)
            
            # Contour doré
            pygame.draw.rect(surf, (180, 150, 80), (cx - 9, cy - 2, 16, 8), 1, border_radius=3)
            
            self.cache[key] = surf
        
        screen.blit(self.cache[key], (x - size // 2, y - size // 2))
        self._draw_health_bar(screen, x, y - 18, 22, hp_ratio, team_id)
    
    def draw_pyramid(self, screen: pygame.Surface, x: int, y: int, team_id: int, 
                     hp_ratio: float = 1.0, level: int = 1):
        """Dessine une Pyramide."""
        base_size = 28
        size = base_size + level * 2
        key = self._get_cache_key(f"pyramid_l{level}", team_id, size)
        
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
                (cx, cy - size // 2),           # Sommet
                (cx - size // 2, cy + size // 3),  # Bas gauche
                (cx + size // 2, cy + size // 3)   # Bas droit
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
        
        # Projectile avec traînée
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
