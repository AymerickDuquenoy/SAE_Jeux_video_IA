# Game/App/renderers/menu_renderer.py
"""Menu rendering for Antique War."""

import pygame


class MenuRenderer:
    """Rendu des menus (principal, options, pause, game_over)."""

    def __init__(self, app, base_renderer):
        self.app = app
        self.base = base_renderer

    def draw_menu(self):
        """Dessine l'écran du menu principal."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        else:
            self.base.draw_center_overlay("Antique War", "")
        
        # Titre
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Antique War", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Antique War", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        # Record
        record_text = f"Record: {self.app.best_time:.1f}s | Kills: {self.app.best_kills}"
        rec = self.app.font_small.render(record_text, True, (255, 245, 220))
        rr = rec.get_rect(center=(self.app.width // 2, self.app.height - 30))
        
        padding = 10
        bg_rect = pygame.Rect(rr.left - padding, rr.top - 4, rr.width + padding * 2, rr.height + 8)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((40, 30, 20, 180))
        self.app.screen.blit(bg_surf, bg_rect)
        self.app.screen.blit(rec, rr)

        # Boutons
        self.app.btn_play.draw(self.app.screen)
        self.app.btn_options.draw(self.app.screen)
        self.app.btn_controls.draw(self.app.screen)
        self.app.btn_quit.draw(self.app.screen)

    def draw_difficulty_select(self):
        """Dessine l'écran de sélection de difficulté."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        
        # Titre
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Difficulte", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Difficulte", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        # Panneau
        panel_w, panel_h = 360, 380
        panel_x = self.app.width // 2 - panel_w // 2
        panel_y = self.app.height // 2 - panel_h // 2 + 30
        self.base.draw_blurred_panel(panel_x, panel_y, panel_w, panel_h, blur_radius=10)
        
        gold_dark = (139, 119, 77)
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        
        # Boutons de difficulté
        btn_w = 260
        btn_h = 45
        btn_x = self.app.width // 2 - btn_w // 2
        btn_y_start = panel_y + 25
        btn_gap = 85
        
        diff_data = [
            ("easy", "Facile", "Revenus ennemi x0.5", (100, 200, 100)),
            ("medium", "Moyen", "Revenus ennemi x1.0", (200, 200, 100)),
            ("hard", "Difficile", "Revenus ennemi x1.5", (255, 180, 80)),
            ("extreme", "Extreme", "Revenus ennemi x2.0", (255, 100, 100)),
        ]
        
        buttons = [self.app.btn_diff_easy, self.app.btn_diff_medium, self.app.btn_diff_hard, self.app.btn_diff_extreme]
        
        for i, (key, label, desc, color) in enumerate(diff_data):
            btn = buttons[i]
            btn.rect = pygame.Rect(btn_x, btn_y_start + i * btn_gap, btn_w, btn_h)
            btn.text = label
            btn.draw(self.app.screen)
            
            desc_surf = self.app.font_small.render(desc, True, color)
            desc_rect = desc_surf.get_rect(centerx=self.app.width // 2, top=btn.rect.bottom + 5)
            self.app.screen.blit(desc_surf, desc_rect)
        
        self.app.btn_back.draw(self.app.screen)

    def draw_options(self):
        """Dessine l'écran des options."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        
        # Titre
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Options", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Options", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        # Panneau
        panel_w = 580
        panel_h = 320
        panel_x = self.app.width // 2 - panel_w // 2
        panel_y = self.app.height // 2 - panel_h // 2
        self.base.draw_blurred_panel(panel_x, panel_y, panel_w, panel_h, blur_radius=10)
        
        gold_dark = (139, 119, 77)
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        
        # Toggles
        toggle_w = 520
        toggle_h = 45
        toggle_x = self.app.width // 2 - toggle_w // 2
        toggle_gap = 90
        
        # Toggle 1 : Lanes
        toggle1_y = panel_y + 25
        self.app.tog_lanes.rect = pygame.Rect(toggle_x, toggle1_y, toggle_w, toggle_h)
        self.app.tog_lanes.draw(self.app.screen)
        desc1_surf = self.app.font_small.render("Chemins des 3 lanes (joueur=cyan, ennemi=orange)", True, (160, 155, 140))
        desc1_rect = desc1_surf.get_rect(centerx=self.app.width // 2, top=self.app.tog_lanes.rect.bottom + 3)
        self.app.screen.blit(desc1_surf, desc1_rect)
        
        # Toggle 2 : Terrain
        toggle2_y = toggle1_y + toggle_gap
        self.app.tog_terrain.rect = pygame.Rect(toggle_x, toggle2_y, toggle_w, toggle_h)
        self.app.tog_terrain.draw(self.app.screen)
        desc2_surf = self.app.font_small.render("Zones lentes (marron) et interdites (rouge)", True, (160, 155, 140))
        desc2_rect = desc2_surf.get_rect(centerx=self.app.width // 2, top=self.app.tog_terrain.rect.bottom + 3)
        self.app.screen.blit(desc2_surf, desc2_rect)
        
        # Toggle 3 : Paths
        toggle3_y = toggle2_y + toggle_gap
        self.app.tog_paths.rect = pygame.Rect(toggle_x, toggle3_y, toggle_w, toggle_h)
        self.app.tog_paths.draw(self.app.screen)
        desc3_surf = self.app.font_small.render("Trajet de chaque unite en temps reel", True, (160, 155, 140))
        desc3_rect = desc3_surf.get_rect(centerx=self.app.width // 2, top=self.app.tog_paths.rect.bottom + 3)
        self.app.screen.blit(desc3_surf, desc3_rect)
        
        self.app.btn_back.draw(self.app.screen)

    def draw_controls(self):
        """Dessine l'écran des commandes."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        
        self.base.draw_blurred_panel(48, 120, self.app.width - 96, self.app.height - 190, blur_radius=10)
        
        # Titre
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Commandes", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Commandes", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        self.app.btn_back.draw(self.app.screen)

        x = 70
        y = 150
        lines = [
            "Déplacement caméra : flèches",
            "Choisir la lane : Z / X / C (ou W / X / C)",
            "Lane cliquable : boutons Lane 1/2/3 en haut",
            "Spawn unités : 1 / 2 / 3",
            "Upgrade pyramide : U",
            "Pause : ESC",
        ]
        for txt in lines:
            surf = self.app.font.render(txt, True, (222, 205, 163))
            self.app.screen.blit(surf, (x, y))
            y += 28

    def draw_pause(self):
        """Dessine l'écran de pause."""
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        overlay.fill((15, 12, 8, 180))
        self.app.screen.blit(overlay, (0, 0))
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)
        bg_dark = (45, 38, 30)
        
        panel_w, panel_h = 320, 340
        panel_x = self.app.width // 2 - panel_w // 2
        panel_y = self.app.height // 2 - panel_h // 2
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((bg_dark[0], bg_dark[1], bg_dark[2], 245))
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=12)
        pygame.draw.rect(self.app.screen, gold_light, (panel_x + 6, panel_y + 6, panel_w - 12, panel_h - 12), 2, border_radius=10)
        
        title_surf = self.app.font_big.render("PAUSE", True, text_gold)
        title_rect = title_surf.get_rect(centerx=self.app.width // 2, top=panel_y + 25)
        self.app.screen.blit(title_surf, title_rect)
        
        sub_surf = self.app.font_small.render("ESC pour reprendre", True, (150, 145, 135))
        sub_rect = sub_surf.get_rect(centerx=self.app.width // 2, top=panel_y + 65)
        self.app.screen.blit(sub_surf, sub_rect)
        
        sep_y = panel_y + 95
        pygame.draw.line(self.app.screen, gold_light, (panel_x + 30, sep_y), (panel_x + panel_w - 30, sep_y), 2)
        
        btn_w, btn_h = 200, 42
        btn_x = self.app.width // 2 - btn_w // 2
        btn_y = panel_y + 115
        btn_gap = 52
        
        self.app.btn_resume.rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        self.app.btn_pause_options.rect = pygame.Rect(btn_x, btn_y + btn_gap, btn_w, btn_h)
        self.app.btn_restart.rect = pygame.Rect(btn_x, btn_y + btn_gap * 2, btn_w, btn_h)
        self.app.btn_menu.rect = pygame.Rect(btn_x, btn_y + btn_gap * 3, btn_w, btn_h)
        
        self.app.btn_resume.draw(self.app.screen)
        self.app.btn_pause_options.draw(self.app.screen)
        self.app.btn_restart.draw(self.app.screen)
        self.app.btn_menu.draw(self.app.screen)

    def draw_game_over(self):
        """Dessine l'écran de fin de partie."""
        overlay = pygame.Surface((self.app.width, self.app.height), pygame.SRCALPHA)
        overlay.fill((15, 12, 8, 200))
        self.app.screen.blit(overlay, (0, 0))
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)
        bg_dark = (45, 38, 30)
        
        panel_w, panel_h = 420, 320
        panel_x = self.app.width // 2 - panel_w // 2
        panel_y = self.app.height // 2 - panel_h // 2 - 20
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((bg_dark[0], bg_dark[1], bg_dark[2], 245))
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=12)
        pygame.draw.rect(self.app.screen, gold_light, (panel_x + 6, panel_y + 6, panel_w - 12, panel_h - 12), 2, border_radius=10)
        
        is_victory = self.app.game_over_text == "VICTORY"
        title_color = (100, 255, 150) if is_victory else (255, 100, 100)
        title_text = "VICTOIRE" if is_victory else "DEFAITE"
        
        title_surf = self.app.font_big.render(title_text, True, title_color)
        title_rect = title_surf.get_rect(centerx=self.app.width // 2, top=panel_y + 25)
        self.app.screen.blit(title_surf, title_rect)
        
        sep_y = panel_y + 75
        pygame.draw.line(self.app.screen, gold_light, (panel_x + 30, sep_y), (panel_x + panel_w - 30, sep_y), 2)
        
        stats_x = panel_x + 40
        stats_y = panel_y + 95
        line_h = 36
        
        label1 = self.app.font.render("Temps de jeu:", True, (180, 170, 150))
        value1 = self.app.font.render(f"{self.app.match_time:.1f}s", True, text_gold)
        self.app.screen.blit(label1, (stats_x, stats_y))
        self.app.screen.blit(value1, (panel_x + panel_w - 40 - value1.get_width(), stats_y))
        stats_y += line_h
        
        label2 = self.app.font.render("Ennemis elimines:", True, (180, 170, 150))
        value2 = self.app.font.render(f"{self.app.enemy_kills}", True, text_gold)
        self.app.screen.blit(label2, (stats_x, stats_y))
        self.app.screen.blit(value2, (panel_x + panel_w - 40 - value2.get_width(), stats_y))
        stats_y += line_h
        
        diff_names = {"easy": "Facile", "medium": "Moyen", "hard": "Difficile", "extreme": "Extreme"}
        diff_name = diff_names.get(self.app.selected_difficulty, "Moyen")
        label3 = self.app.font.render("Difficulte:", True, (180, 170, 150))
        value3 = self.app.font.render(diff_name, True, text_gold)
        self.app.screen.blit(label3, (stats_x, stats_y))
        self.app.screen.blit(value3, (panel_x + panel_w - 40 - value3.get_width(), stats_y))
        stats_y += line_h + 5
        
        pygame.draw.line(self.app.screen, gold_dark, (panel_x + 30, stats_y - 5), (panel_x + panel_w - 30, stats_y - 5), 1)
        stats_y += 5
        
        score = int(self.app.match_time * 10 + self.app.enemy_kills * 50)
        label4 = self.app.font.render("Score:", True, (255, 220, 100))
        value4 = self.app.font_big.render(f"{score}", True, (255, 220, 100))
        self.app.screen.blit(label4, (stats_x, stats_y + 5))
        self.app.screen.blit(value4, (panel_x + panel_w - 40 - value4.get_width(), stats_y))
        stats_y += 50
        
        record_txt = f"Record: {self.app.best_time:.1f}s  |  Meilleur kills: {self.app.best_kills}"
        record_surf = self.app.font_small.render(record_txt, True, (150, 145, 135))
        record_rect = record_surf.get_rect(centerx=self.app.width // 2, top=stats_y)
        self.app.screen.blit(record_surf, record_rect)
        
        if self.app.match_time >= self.app.best_time or self.app.enemy_kills >= self.app.best_kills:
            stats_y += 28
            new_rec = self.app.font.render("NOUVEAU RECORD!", True, (255, 220, 80))
            rec_rect = new_rec.get_rect(centerx=self.app.width // 2, top=stats_y)
            bg_rect = rec_rect.inflate(24, 10)
            pygame.draw.rect(self.app.screen, (80, 60, 30), bg_rect, border_radius=6)
            pygame.draw.rect(self.app.screen, gold_light, bg_rect, 2, border_radius=6)
            self.app.screen.blit(new_rec, rec_rect)

        btn_w, btn_h = 180, 45
        btn_y = panel_y + panel_h + 25
        
        self.app.btn_restart.rect = pygame.Rect(self.app.width // 2 - btn_w // 2, btn_y, btn_w, btn_h)
        self.app.btn_menu.rect = pygame.Rect(self.app.width // 2 - btn_w // 2, btn_y + btn_h + 15, btn_w, btn_h)
        
        self.app.btn_restart.draw(self.app.screen)
        self.app.btn_menu.draw(self.app.screen)
