# Game/App/renderers/hud_renderer.py
"""HUD rendering for Antique War."""

import os
import pygame
import esper

from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.pyramidLevel import PyramidLevel
from Game.Ecs.Components.incomeRate import IncomeRate


class HUDRenderer:
    """Rendu du HUD (interface en jeu)."""

    def __init__(self, app):
        self.app = app

    def draw_whip_icon(self, x: int, y: int, size: int = 20, with_background: bool = True):
        """Dessine l'icône du fouet depuis le PNG."""
        if with_background:
            bg_size = size - 2
            bg_x = x + 1
            bg_y = y + 1
            pygame.draw.rect(self.app.screen, (130, 115, 90), (bg_x, bg_y, bg_size, bg_size), border_radius=6)
            pygame.draw.rect(self.app.screen, (180, 155, 100), (bg_x, bg_y, bg_size, bg_size), 2, border_radius=6)
        
        if size in self.app.whip_icons_cache and self.app.whip_icons_cache[size] is not None:
            self.app.screen.blit(self.app.whip_icons_cache[size], (x, y))
            return
        
        if self.app.whip_icon is None:
            try:
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites", "fouet.png"),
                    os.path.join("Game", "assets", "sprites", "fouet.png"),
                    os.path.join("assets", "sprites", "fouet.png"),
                ]
                for whip_path in possible_paths:
                    if os.path.exists(whip_path):
                        self.app.whip_icon = pygame.image.load(whip_path).convert_alpha()
                        break
                else:
                    self.app.whip_icon = False
            except Exception as e:
                print(f"[WARN] Failed to load fouet.png: {e}")
                self.app.whip_icon = False
        
        if self.app.whip_icon and self.app.whip_icon is not False:
            orig_w, orig_h = self.app.whip_icon.get_size()
            scale = size / orig_h
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            
            if new_w > 0 and new_h > 0:
                scaled = pygame.transform.smoothscale(self.app.whip_icon, (new_w, new_h))
                self.app.whip_icons_cache[size] = scaled
                offset_x = (size - new_w) // 2
                self.app.screen.blit(scaled, (x + offset_x, y))
                return
        
        # Fallback
        handle_color = (139, 90, 43)
        pygame.draw.rect(self.app.screen, handle_color, (x, y + size//2 - 3, 8, 6), border_radius=2)
        whip_color = (180, 140, 80)
        points = [(x + 8, y + size//2), (x + 12, y + size//3), (x + 16, y + size//4), (x + size, y + 2)]
        pygame.draw.lines(self.app.screen, whip_color, False, points, 3)
        pygame.draw.circle(self.app.screen, (220, 180, 100), (x + size, y + 2), 2)

    def get_unit_icon(self, unit_key: str, size: int = 32) -> pygame.Surface:
        """Retourne une icône miniature de l'unité depuis le sprite."""
        cache_key = f"icon_{unit_key}_{size}"
        
        if cache_key in self.app.unit_icons_cache:
            return self.app.unit_icons_cache[cache_key]
        
        icon = pygame.Surface((size, size), pygame.SRCALPHA)
        
        try:
            from Game.Rendering.sprite_renderer import sprite_renderer
            sprite_renderer._load_sprites()
            
            sprite_map = {"S": "momie_1", "M": "dromadaire_1", "L": "sphinx_1"}
            sprite_key = sprite_map.get(unit_key, "momie_1")
            
            frames = sprite_renderer.frames.get(sprite_key)
            if frames and frames[0]:
                orig = frames[0]
                orig_w, orig_h = orig.get_size()
                scale = min(size / orig_w, size / orig_h) * 0.9
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                scaled = pygame.transform.smoothscale(orig, (new_w, new_h))
                icon.blit(scaled, ((size - new_w) // 2, (size - new_h) // 2))
                self.app.unit_icons_cache[cache_key] = icon
                return icon
        except Exception:
            pass
        
        # Fallback
        colors = {"S": (200, 180, 140), "M": (180, 140, 100), "L": (220, 200, 150)}
        color = colors.get(unit_key, (200, 180, 140))
        
        if unit_key == "S":
            pygame.draw.circle(icon, color, (size//2, size//2), size//3)
            pygame.draw.circle(icon, (255, 255, 200), (size//2 - 3, size//2 - 3), 2)
        elif unit_key == "M":
            pygame.draw.ellipse(icon, color, (4, 8, size - 8, size - 12))
            pygame.draw.circle(icon, color, (size//2 + 6, 8), 4)
        else:
            points = [(size//2, 4), (4, size - 4), (size - 4, size - 4)]
            pygame.draw.polygon(icon, color, points)
        
        self.app.unit_icons_cache[cache_key] = icon
        return icon

    def draw_upgrade_icon(self, surface: pygame.Surface, x: int, y: int, size: int = 24):
        """Dessine une icône d'upgrade (flèche vers le haut)."""
        cx, cy = x + size // 2, y + size // 2
        
        arrow_color = (255, 220, 100)
        points = [
            (cx, y + 3), (cx - 8, y + 12), (cx - 4, y + 12),
            (cx - 4, y + size - 3), (cx + 4, y + size - 3),
            (cx + 4, y + 12), (cx + 8, y + 12),
        ]
        pygame.draw.polygon(surface, arrow_color, points)
        pygame.draw.polygon(surface, (200, 170, 60), points, 2)
        pygame.draw.circle(surface, (255, 255, 200), (cx, y + 5), 3)

    def draw_lane_selector(self):
        """Dessine les boutons de sélection de lane."""
        selected = self.app._get_selected_lane_index()
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        sand_bg = (58, 52, 45)
        sand_active = (90, 75, 55)
        text_gold = (222, 205, 163)
        
        for i, r in enumerate(self.app.lane_btn_rects):
            active = (i == selected)
            bg = sand_active if active else sand_bg
            pygame.draw.rect(self.app.screen, bg, r, border_radius=6)
            
            border_color = gold_light if active else gold_dark
            pygame.draw.rect(self.app.screen, border_color, r, width=3, border_radius=6)
            
            if active:
                inner = r.inflate(-6, -6)
                pygame.draw.rect(self.app.screen, gold_light, inner, width=2, border_radius=4)
            
            txt_col = (255, 230, 150) if active else text_gold
            s = self.app.font_small.render(f"Lane {i+1}", True, txt_col)
            tr = s.get_rect(center=r.center)
            self.app.screen.blit(s, tr)

    def draw_hud_minimal(self):
        """Dessine le HUD principal avec style égyptien."""
        if not self.app.player_pyramid_eid or not self.app.enemy_pyramid_eid:
            return

        if self.app.world:
            self.app.world._activate()

        wallet = esper.component_for_entity(self.app.player_pyramid_eid, Wallet)
        player_hp = esper.component_for_entity(self.app.player_pyramid_eid, Health)
        enemy_hp = esper.component_for_entity(self.app.enemy_pyramid_eid, Health)

        try:
            income = esper.component_for_entity(self.app.player_pyramid_eid, IncomeRate)
            income_rate = income.effective_rate if hasattr(income, 'effective_rate') else income.rate
        except Exception:
            income_rate = 2.5

        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)
        text_light = (255, 245, 220)
        bg_dark = (40, 35, 30, 220)
        
        # Panneau ressources + HP
        panel_w, panel_h = 280, 90
        panel_x, panel_y = 12, 12
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(bg_dark)
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=8)
        pygame.draw.rect(self.app.screen, gold_light, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 2, border_radius=6)
        
        # Ressources
        self.draw_whip_icon(panel_x + 12, panel_y + 8, 22, with_background=False)
        
        fouet_text = f"{int(wallet.solde)}"
        prod_text = f"+{income_rate:.1f}/s"
        
        fouet_surf = self.app.font.render(fouet_text, True, (255, 215, 80))
        prod_surf = self.app.font_small.render(prod_text, True, (150, 220, 150))
        
        self.app.screen.blit(fouet_surf, (panel_x + 55, panel_y + 12))
        self.app.screen.blit(prod_surf, (panel_x + 55 + fouet_surf.get_width() + 8, panel_y + 16))
        
        # Barre de vie joueur
        bar_y = panel_y + 40
        bar_w = 120
        bar_h = 14
        
        you_label = self.app.font_small.render("Vous", True, text_gold)
        self.app.screen.blit(you_label, (panel_x + 15, bar_y - 1))
        
        bar_x = panel_x + 55
        hp_ratio = player_hp.hp / max(1, player_hp.hp_max)
        pygame.draw.rect(self.app.screen, (50, 45, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = max(0, int((bar_w - 4) * hp_ratio))
        if fill_w > 0:
            pygame.draw.rect(self.app.screen, (80, 180, 120), (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=2)
        pygame.draw.rect(self.app.screen, gold_dark, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)
        
        hp_text = self.app.font_small.render(f"{player_hp.hp}/{player_hp.hp_max}", True, text_light)
        self.app.screen.blit(hp_text, (bar_x + bar_w + 6, bar_y - 1))
        
        # Barre de vie ennemi (masquée en mode 1v1 car présente dans le HUD P2)
        if self.app.game_mode != "1v1":
            bar_y = panel_y + 62
            
            enemy_label = self.app.font_small.render("Ennemi", True, (220, 150, 150))
            self.app.screen.blit(enemy_label, (panel_x + 15, bar_y - 1))
            
            bar_x = panel_x + 70
            bar_w = 105
            hp_ratio = enemy_hp.hp / max(1, enemy_hp.hp_max)
            pygame.draw.rect(self.app.screen, (50, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            fill_w = max(0, int((bar_w - 4) * hp_ratio))
            if fill_w > 0:
                pygame.draw.rect(self.app.screen, (220, 80, 80), (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=2)
            pygame.draw.rect(self.app.screen, (160, 100, 100), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)
            
            hp_text = self.app.font_small.render(f"{enemy_hp.hp}/{enemy_hp.hp_max}", True, (255, 200, 200))
            self.app.screen.blit(hp_text, (bar_x + bar_w + 6, bar_y - 1))
        
        # Boutons unités
        units_y = panel_y + panel_h + 10
        btn_size = 50
        btn_gap = 8
        
        try:
            unit_data = {
                "S": {"cost": int(self.app.factory.compute_unit_stats("S").cost), "key": "1", "name": "Momie"},
                "M": {"cost": int(self.app.factory.compute_unit_stats("M").cost), "key": "2", "name": "Dromadaire"},
                "L": {"cost": int(self.app.factory.compute_unit_stats("L").cost), "key": "3", "name": "Sphinx"},
            }
        except:
            unit_data = {
                "S": {"cost": 80, "key": "1", "name": "Momie"},
                "M": {"cost": 120, "key": "2", "name": "Dromadaire"},
                "L": {"cost": 180, "key": "3", "name": "Sphinx"},
            }
        
        btn_x = panel_x
        for unit_key, data in unit_data.items():
            cost = data["cost"]
            can_afford = wallet.solde >= cost
            
            btn_rect = pygame.Rect(btn_x, units_y, btn_size, btn_size + 18)
            self.app.unit_btn_rects[unit_key] = btn_rect
            
            if can_afford:
                bg_color = (55, 50, 42, 230)
                border_color = gold_light
            else:
                bg_color = (45, 40, 38, 200)
                border_color = (100, 80, 60)
            
            btn_surf = pygame.Surface((btn_size, btn_size + 18), pygame.SRCALPHA)
            btn_surf.fill(bg_color)
            self.app.screen.blit(btn_surf, (btn_x, units_y))
            pygame.draw.rect(self.app.screen, border_color, btn_rect, 2, border_radius=6)
            
            icon = self.get_unit_icon(unit_key, btn_size - 8)
            icon_x = btn_x + 4
            icon_y = units_y + 2
            self.app.screen.blit(icon, (icon_x, icon_y))
            
            cost_color = (150, 220, 150) if can_afford else (180, 100, 100)
            cost_text = self.app.font_small.render(f"{cost}", True, cost_color)
            cost_rect = cost_text.get_rect(centerx=btn_x + btn_size // 2, top=units_y + btn_size - 2)
            self.app.screen.blit(cost_text, cost_rect)
            
            key_text = self.app.font_small.render(data["key"], True, (180, 170, 150))
            self.app.screen.blit(key_text, (btn_x + 3, units_y + 3))
            
            btn_x += btn_size + btn_gap
        
        # Bouton upgrade
        upgrade_x = btn_x + 5
        upgrade_w = 55
        upgrade_h = btn_size + 18
        
        try:
            pyr_level = esper.component_for_entity(self.app.player_pyramid_eid, PyramidLevel)
            current_level = pyr_level.level
        except:
            current_level = 1
        
        max_level = int(self.app.balance.get("pyramid", {}).get("level_max", 5))
        upgrade_costs = self.app.balance.get("pyramid", {}).get("upgrade_costs", [100, 125, 150, 175, 200])
        
        can_upgrade = current_level < max_level
        if can_upgrade and current_level - 1 < len(upgrade_costs):
            upgrade_cost = upgrade_costs[current_level - 1]
            can_afford_upgrade = wallet.solde >= upgrade_cost
        else:
            upgrade_cost = 0
            can_afford_upgrade = False
        
        self.app.upgrade_btn_rect = pygame.Rect(upgrade_x, units_y, upgrade_w, upgrade_h)
        
        if can_upgrade and can_afford_upgrade:
            bg_color = (60, 55, 40, 230)
            border_color = (200, 180, 100)
        elif can_upgrade:
            bg_color = (50, 45, 40, 200)
            border_color = gold_dark
        else:
            bg_color = (40, 40, 40, 180)
            border_color = (80, 80, 80)
        
        upgrade_surf = pygame.Surface((upgrade_w, upgrade_h), pygame.SRCALPHA)
        upgrade_surf.fill(bg_color)
        self.app.screen.blit(upgrade_surf, (upgrade_x, units_y))
        pygame.draw.rect(self.app.screen, border_color, self.app.upgrade_btn_rect, 2, border_radius=6)
        
        self.draw_upgrade_icon(self.app.screen, upgrade_x + (upgrade_w - 28) // 2, units_y + 5, 28)
        
        if can_upgrade:
            level_text = self.app.font_small.render(f"Nv.{current_level + 1}", True, text_gold)
            cost_color = (150, 220, 150) if can_afford_upgrade else (180, 100, 100)
            cost_text = self.app.font_small.render(f"{upgrade_cost}", True, cost_color)
        else:
            level_text = self.app.font_small.render("MAX", True, (180, 180, 180))
            cost_text = None
        
        level_rect = level_text.get_rect(centerx=upgrade_x + upgrade_w // 2, top=units_y + 36)
        self.app.screen.blit(level_text, level_rect)
        
        if cost_text:
            cost_rect = cost_text.get_rect(centerx=upgrade_x + upgrade_w // 2, top=units_y + btn_size + 2)
            self.app.screen.blit(cost_text, cost_rect)
        
        u_text = self.app.font_small.render("U", True, (180, 170, 150))
        self.app.screen.blit(u_text, (upgrade_x + 3, units_y + 3))

        # Sélecteur de lane
        lane_y = units_y + btn_size + 28
        lane_bw = 75
        lane_bh = 28
        lane_gap = 8
        
        self.app.lane_btn_rects = [
            pygame.Rect(panel_x + i * (lane_bw + lane_gap), lane_y, lane_bw, lane_bh)
            for i in range(3)
        ]
        
        self.draw_lane_selector()

        # Message d'événement
        if self.app.random_event_system:
            msg = self.app.random_event_system.get_message()
            if msg:
                event_surf = self.app.font_big.render(msg, True, (255, 220, 80))
                event_rect = event_surf.get_rect(center=(self.app.base_width // 2, 80))
                bg_rect = event_rect.inflate(30, 15)
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surf.fill((40, 30, 20, 220))
                self.app.screen.blit(bg_surf, bg_rect.topleft)
                pygame.draw.rect(self.app.screen, gold_light, bg_rect, 3, border_radius=8)
                self.app.screen.blit(event_surf, event_rect)

    def draw_hud_advanced(self, base_renderer):
        """Dessine le HUD avancé avec infos de debug."""
        base_renderer.draw_panel(12, 112, 640, 94, alpha=100)
        x = 22
        y = 120

        l1 = self.app.font_small.render(
            f"Map: {self.app.map_name} | Seed: {self.app.map_seed} | "
            f"open={self.app.zone_counts.get('open', 0)} dusty={self.app.zone_counts.get('dusty', 0)} interdit={self.app.zone_counts.get('forbidden', 0)}",
            True, (220, 220, 220)
        )
        l2 = self.app.font_small.render(
            f"Match: {self.app.match_time:.1f}s | Kills: {self.app.enemy_kills}",
            True, (220, 220, 220)
        )
        
        if self.app.enemy_spawner_system:
            diff_txt = self.app.enemy_spawner_system.hud_line()
        else:
            diff_txt = "Spawner: N/A"
        l3 = self.app.font_small.render(diff_txt, True, (220, 220, 220))

        self.app.screen.blit(l1, (x, y))
        self.app.screen.blit(l2, (x, y + 22))
        self.app.screen.blit(l3, (x, y + 44))

    def draw_hud_player2(self):
        """Dessine le HUD du joueur 2 (à droite) en mode 1v1 - miroir du P1."""
        if self.app.game_mode != "1v1":
            return
            
        if not self.app.enemy_pyramid_eid:
            return

        if self.app.world:
            self.app.world._activate()

        try:
            wallet = esper.component_for_entity(self.app.enemy_pyramid_eid, Wallet)
            p2_hp = esper.component_for_entity(self.app.enemy_pyramid_eid, Health)
        except:
            return
            
        try:
            income = esper.component_for_entity(self.app.enemy_pyramid_eid, IncomeRate)
            income_rate = income.effective_rate if hasattr(income, 'effective_rate') else income.rate
        except:
            income_rate = 2.5

        # Couleurs style bleu/cyan pour différencier du P1
        blue_dark = (77, 100, 139)
        blue_light = (101, 140, 179)
        text_blue = (163, 200, 222)
        text_light = (220, 240, 255)
        bg_dark = (30, 38, 48, 220)
        
        # Panneau ressources + HP (miroir à droite)
        panel_w, panel_h = 280, 90
        panel_x = self.app.base_width - panel_w - 12
        panel_y = 12
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(bg_dark)
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.app.screen, blue_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=8)
        pygame.draw.rect(self.app.screen, blue_light, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 2, border_radius=6)
        
        # Titre "JOUEUR 2"
        title = self.app.font_small.render("JOUEUR 2", True, text_blue)
        self.app.screen.blit(title, (panel_x + 12, panel_y + 6))
        
        # Ressources
        self.draw_whip_icon(panel_x + 12, panel_y + 26, 22, with_background=False)
        
        fouet_text = f"{int(wallet.solde)}"
        prod_text = f"+{income_rate:.1f}/s"
        
        fouet_surf = self.app.font.render(fouet_text, True, (80, 180, 255))
        prod_surf = self.app.font_small.render(prod_text, True, (100, 200, 180))
        
        self.app.screen.blit(fouet_surf, (panel_x + 55, panel_y + 30))
        self.app.screen.blit(prod_surf, (panel_x + 55 + fouet_surf.get_width() + 8, panel_y + 34))
        
        # Barre de vie P2
        bar_y = panel_y + 58
        bar_w = 180
        bar_h = 14
        bar_x = panel_x + 80
        
        hp_label = self.app.font_small.render("Pyramide", True, text_blue)
        self.app.screen.blit(hp_label, (panel_x + 15, bar_y - 1))
        
        hp_ratio = p2_hp.hp / max(1, p2_hp.hp_max)
        pygame.draw.rect(self.app.screen, (40, 50, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = max(0, int((bar_w - 4) * hp_ratio))
        if fill_w > 0:
            pygame.draw.rect(self.app.screen, (80, 150, 220), (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=2)
        pygame.draw.rect(self.app.screen, blue_dark, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=3)
        
        # Boutons P2 : [Upgrade] [S] [M] [L] alignés à droite
        units_y = panel_y + panel_h + 10
        btn_size = 50
        btn_gap = 8
        upgrade_w = 55
        upgrade_h = btn_size + 18
        
        try:
            unit_data = {
                "S": {"cost": int(self.app.factory.compute_unit_stats("S").cost), "key": "7", "name": "Momie"},
                "M": {"cost": int(self.app.factory.compute_unit_stats("M").cost), "key": "8", "name": "Dromadaire"},
                "L": {"cost": int(self.app.factory.compute_unit_stats("L").cost), "key": "9", "name": "Sphinx"},
            }
        except:
            unit_data = {
                "S": {"cost": 80, "key": "7", "name": "Momie"},
                "M": {"cost": 120, "key": "8", "name": "Dromadaire"},
                "L": {"cost": 180, "key": "9", "name": "Sphinx"},
            }
        
        # Calculer largeur totale : upgrade + 3 boutons
        total_units_w = len(unit_data) * btn_size + (len(unit_data) - 1) * btn_gap
        total_w = upgrade_w + btn_gap + total_units_w
        
        # Position de départ (bouton upgrade à gauche)
        start_x = self.app.base_width - 12 - total_w
        
        # === BOUTON UPGRADE P2 (à gauche) ===
        upgrade_x = start_x
        
        try:
            pyr_level = esper.component_for_entity(self.app.enemy_pyramid_eid, PyramidLevel)
            current_level = pyr_level.level
        except:
            current_level = 1
        
        max_level = int(self.app.balance.get("pyramid", {}).get("level_max", 5))
        upgrade_costs = self.app.balance.get("pyramid", {}).get("upgrade_costs", [100, 125, 150, 175, 200])
        
        can_upgrade = current_level < max_level
        if can_upgrade and current_level - 1 < len(upgrade_costs):
            upgrade_cost = upgrade_costs[current_level - 1]
            can_afford_upgrade = wallet.solde >= upgrade_cost
        else:
            upgrade_cost = 0
            can_afford_upgrade = False
        
        self.app.upgrade_btn_rect_p2 = pygame.Rect(upgrade_x, units_y, upgrade_w, upgrade_h)
        
        if can_upgrade and can_afford_upgrade:
            bg_color = (40, 55, 70, 230)
            border_color = (100, 180, 220)
        elif can_upgrade:
            bg_color = (40, 50, 60, 200)
            border_color = blue_dark
        else:
            bg_color = (40, 40, 45, 180)
            border_color = (60, 80, 100)
        
        upgrade_surf = pygame.Surface((upgrade_w, upgrade_h), pygame.SRCALPHA)
        upgrade_surf.fill(bg_color)
        self.app.screen.blit(upgrade_surf, (upgrade_x, units_y))
        pygame.draw.rect(self.app.screen, border_color, self.app.upgrade_btn_rect_p2, 2, border_radius=6)
        
        self.draw_upgrade_icon(self.app.screen, upgrade_x + (upgrade_w - 28) // 2, units_y + 5, 28)
        
        if can_upgrade:
            level_text = self.app.font_small.render(f"Nv.{current_level + 1}", True, text_blue)
            cost_color = (100, 200, 150) if can_afford_upgrade else (180, 100, 100)
            cost_text = self.app.font_small.render(f"{upgrade_cost}", True, cost_color)
        else:
            level_text = self.app.font_small.render("MAX", True, (150, 180, 200))
            cost_text = None
        
        level_rect = level_text.get_rect(centerx=upgrade_x + upgrade_w // 2, top=units_y + 36)
        self.app.screen.blit(level_text, level_rect)
        
        if cost_text:
            cost_rect = cost_text.get_rect(centerx=upgrade_x + upgrade_w // 2, top=units_y + btn_size + 2)
            self.app.screen.blit(cost_text, cost_rect)
        
        # === BOUTONS UNITÉS P2 (à droite de l'upgrade) ===
        btn_x = upgrade_x + upgrade_w + btn_gap
        
        self.app.unit_btn_rects_p2 = {}
        for unit_key, data in unit_data.items():
            cost = data["cost"]
            can_afford = wallet.solde >= cost
            
            btn_rect = pygame.Rect(btn_x, units_y, btn_size, btn_size + 18)
            self.app.unit_btn_rects_p2[unit_key] = btn_rect
            
            if can_afford:
                bg_color = (42, 50, 65, 230)
                border_color = blue_light
            else:
                bg_color = (38, 42, 50, 200)
                border_color = (60, 80, 100)
            
            btn_surf = pygame.Surface((btn_size, btn_size + 18), pygame.SRCALPHA)
            btn_surf.fill(bg_color)
            self.app.screen.blit(btn_surf, (btn_x, units_y))
            pygame.draw.rect(self.app.screen, border_color, btn_rect, 2, border_radius=6)
            
            icon = self.get_unit_icon(unit_key, btn_size - 8)
            icon_x = btn_x + 4
            icon_y = units_y + 2
            self.app.screen.blit(icon, (icon_x, icon_y))
            
            cost_color = (100, 200, 150) if can_afford else (180, 100, 100)
            cost_text = self.app.font_small.render(f"{cost}", True, cost_color)
            cost_rect = cost_text.get_rect(centerx=btn_x + btn_size // 2, top=units_y + btn_size - 2)
            self.app.screen.blit(cost_text, cost_rect)
            
            key_text = self.app.font_small.render(data["key"], True, (150, 170, 190))
            self.app.screen.blit(key_text, (btn_x + 3, units_y + 3))
            
            btn_x += btn_size + btn_gap
        
        # Sélecteur de lanes P2
        lane_y = units_y + btn_size + 28
        lane_bw = 55
        lane_bh = 28
        lane_gap = 8
        
        total_lane_w = 3 * lane_bw + 2 * lane_gap
        lane_x_start = self.app.base_width - 12 - total_lane_w
        
        selected_p2 = self.app.selected_lane_idx_p2
        lane_keys = ["I", "O", "P"]
        
        self.app.lane_btn_rects_p2 = []
        for i in range(3):
            r = pygame.Rect(lane_x_start + i * (lane_bw + lane_gap), lane_y, lane_bw, lane_bh)
            self.app.lane_btn_rects_p2.append(r)
            
            active = (i == selected_p2)
            bg = (70, 90, 110) if active else (45, 55, 65)
            pygame.draw.rect(self.app.screen, bg, r, border_radius=6)
            
            border = blue_light if active else blue_dark
            pygame.draw.rect(self.app.screen, border, r, width=3, border_radius=6)
            
            if active:
                inner = r.inflate(-6, -6)
                pygame.draw.rect(self.app.screen, blue_light, inner, width=2, border_radius=4)
            
            txt_col = (180, 220, 255) if active else text_blue
            s = self.app.font_small.render(f"{lane_keys[i]}", True, txt_col)
            tr = s.get_rect(center=r.center)
            self.app.screen.blit(s, tr)
