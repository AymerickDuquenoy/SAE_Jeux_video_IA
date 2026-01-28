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
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Antique War", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        # Record
        record_text = f"Record: {self.app.best_time:.1f}s | Kills: {self.app.best_kills}"
        rec = self.app.font_small.render(record_text, True, (255, 245, 220))
        rr = rec.get_rect(center=(self.app.base_width // 2, self.app.base_height - 30))
        
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

    def draw_mode_select(self):
        """Dessine l'écran de sélection du mode de jeu."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Mode de Jeu", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Mode de Jeu", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        # Panneau
        panel_w, panel_h = 420, 300
        panel_x = self.app.base_width // 2 - panel_w // 2
        panel_y = self.app.base_height // 2 - panel_h // 2 + 20
        self.base.draw_blurred_panel(panel_x, panel_y, panel_w, panel_h, blur_radius=10)
        
        gold_dark = (139, 119, 77)
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        
        # Solo vs IA
        self.app.btn_mode_solo.draw(self.app.screen)
        desc1 = self.app.font_small.render("Affrontez l'IA avec difficulte variable", True, (180, 200, 150))
        desc1_rect = desc1.get_rect(centerx=self.app.base_width // 2, top=self.app.btn_mode_solo.rect.bottom + 8)
        self.app.screen.blit(desc1, desc1_rect)
        
        # 1v1 Local
        self.app.btn_mode_1v1.draw(self.app.screen)
        desc2 = self.app.font_small.render("2 joueurs sur le meme clavier", True, (150, 200, 255))
        desc2_rect = desc2.get_rect(centerx=self.app.base_width // 2, top=self.app.btn_mode_1v1.rect.bottom + 8)
        self.app.screen.blit(desc2, desc2_rect)
        
        # Contrôles P2
        controls = self.app.font_small.render("J2: I/O/P (lanes) + 7/8/9 (unites)", True, (150, 180, 220))
        controls_rect = controls.get_rect(centerx=self.app.base_width // 2, top=desc2_rect.bottom + 5)
        self.app.screen.blit(controls, controls_rect)
        
        self.app.btn_back.draw(self.app.screen)

    def draw_difficulty_select(self):
        """Dessine l'écran de sélection de difficulté."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        
        # Titre
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Difficulte", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Difficulte", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        # Panneau
        panel_w, panel_h = 360, 380
        panel_x = self.app.base_width // 2 - panel_w // 2
        panel_y = self.app.base_height // 2 - panel_h // 2 + 30
        self.base.draw_blurred_panel(panel_x, panel_y, panel_w, panel_h, blur_radius=10)
        
        gold_dark = (139, 119, 77)
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        
        # Boutons de difficulté
        btn_w = 260
        btn_h = 45
        btn_x = self.app.base_width // 2 - btn_w // 2
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
            desc_rect = desc_surf.get_rect(centerx=self.app.base_width // 2, top=btn.rect.bottom + 5)
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
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2 + 3, 53))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Options", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2, 50))
        self.app.screen.blit(title_surf, title_rect)
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        
        # Panneau gauche : Affichage
        panel1_w = 280
        panel1_h = 260
        panel1_x = self.app.base_width // 2 - panel1_w - 15
        panel1_y = 120
        self.base.draw_blurred_panel(panel1_x, panel1_y, panel1_w, panel1_h, blur_radius=10)
        pygame.draw.rect(self.app.screen, gold_dark, (panel1_x, panel1_y, panel1_w, panel1_h), 3, border_radius=10)
        
        # Titre panneau Affichage
        cat1_surf = self.app.font.render("AFFICHAGE", True, gold_light)
        cat1_rect = cat1_surf.get_rect(centerx=panel1_x + panel1_w // 2, top=panel1_y + 12)
        self.app.screen.blit(cat1_surf, cat1_rect)
        
        # Séparateur
        pygame.draw.line(self.app.screen, gold_dark, (panel1_x + 15, panel1_y + 40), (panel1_x + panel1_w - 15, panel1_y + 40), 2)
        
        # Toggle plein écran
        toggle_w = panel1_w - 30
        toggle_h = 42
        toggle_x = panel1_x + 15
        toggle1_y = panel1_y + 55
        
        self.app.tog_fullscreen.rect = pygame.Rect(toggle_x, toggle1_y, toggle_w, toggle_h)
        self.app.tog_fullscreen.draw(self.app.screen)
        
        # Sélecteur de résolution (pour le mode fenêtré)
        toggle2_y = toggle1_y + toggle_h + 12
        self.app.sel_resolution.rect = pygame.Rect(toggle_x, toggle2_y, toggle_w, toggle_h)
        self.app.sel_resolution.draw(self.app.screen)
        
        # Bouton Appliquer
        btn_w = 140
        btn_h = 40
        btn_x = panel1_x + (panel1_w - btn_w) // 2
        btn_y = panel1_y + panel1_h - btn_h - 20
        self.app.btn_apply_display.rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        self.app.btn_apply_display.draw(self.app.screen)
        
        # Panneau droit : Jeu
        panel2_w = 280
        panel2_h = 260
        panel2_x = self.app.base_width // 2 + 15
        panel2_y = 120
        self.base.draw_blurred_panel(panel2_x, panel2_y, panel2_w, panel2_h, blur_radius=10)
        pygame.draw.rect(self.app.screen, gold_dark, (panel2_x, panel2_y, panel2_w, panel2_h), 3, border_radius=10)
        
        # Titre panneau Jeu
        cat2_surf = self.app.font.render("JEU", True, gold_light)
        cat2_rect = cat2_surf.get_rect(centerx=panel2_x + panel2_w // 2, top=panel2_y + 12)
        self.app.screen.blit(cat2_surf, cat2_rect)
        
        # Séparateur
        pygame.draw.line(self.app.screen, gold_dark, (panel2_x + 15, panel2_y + 40), (panel2_x + panel2_w - 15, panel2_y + 40), 2)
        
        # Toggles du jeu (labels courts)
        toggle_x2 = panel2_x + 15
        toggle_w2 = panel2_w - 30
        toggle_h2 = 42
        toggle_gap = 52
        
        toggle1_y2 = panel2_y + 55
        self.app.tog_lanes.rect = pygame.Rect(toggle_x2, toggle1_y2, toggle_w2, toggle_h2)
        self.app.tog_lanes.draw(self.app.screen)
        
        toggle2_y2 = toggle1_y2 + toggle_gap
        self.app.tog_terrain.rect = pygame.Rect(toggle_x2, toggle2_y2, toggle_w2, toggle_h2)
        self.app.tog_terrain.draw(self.app.screen)
        
        toggle3_y2 = toggle2_y2 + toggle_gap
        self.app.tog_paths.rect = pygame.Rect(toggle_x2, toggle3_y2, toggle_w2, toggle_h2)
        self.app.tog_paths.draw(self.app.screen)
        
        # Panneau central bas : Audio
        panel3_w = 280
        panel3_h = 140
        panel3_x = self.app.base_width // 2 - panel3_w // 2
        panel3_y = 395
        self.base.draw_blurred_panel(panel3_x, panel3_y, panel3_w, panel3_h, blur_radius=10)
        pygame.draw.rect(self.app.screen, gold_dark, (panel3_x, panel3_y, panel3_w, panel3_h), 3, border_radius=10)
        
        # Titre panneau Audio
        cat3_surf = self.app.font.render("AUDIO", True, gold_light)
        cat3_rect = cat3_surf.get_rect(centerx=panel3_x + panel3_w // 2, top=panel3_y + 12)
        self.app.screen.blit(cat3_surf, cat3_rect)
        
        # Séparateur
        pygame.draw.line(self.app.screen, gold_dark, (panel3_x + 15, panel3_y + 40), (panel3_x + panel3_w - 15, panel3_y + 40), 2)
        
        # Toggles audio
        toggle_x3 = panel3_x + 15
        toggle_w3 = panel3_w - 30
        toggle_h3 = 38
        toggle_gap3 = 45
        
        toggle1_y3 = panel3_y + 52
        self.app.tog_sound.rect = pygame.Rect(toggle_x3, toggle1_y3, toggle_w3, toggle_h3)
        self.app.tog_sound.draw(self.app.screen)
        
        toggle2_y3 = toggle1_y3 + toggle_gap3
        self.app.tog_music.rect = pygame.Rect(toggle_x3, toggle2_y3, toggle_w3, toggle_h3)
        self.app.tog_music.draw(self.app.screen)
        
        self.app.btn_back.draw(self.app.screen)

    def draw_controls(self):
        """Dessine l'écran des commandes."""
        if self.app.menu_background:
            self.app.screen.blit(self.app.menu_background, (0, 0))
        
        # Titre
        title_color = (222, 205, 163)
        title_shadow = (80, 60, 40)
        
        title_surf = self.app.font_title.render("Commandes", True, title_shadow)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2 + 3, 63))
        self.app.screen.blit(title_surf, title_rect)
        
        title_surf = self.app.font_title.render("Commandes", True, title_color)
        title_rect = title_surf.get_rect(center=(self.app.base_width // 2, 60))
        self.app.screen.blit(title_surf, title_rect)
        
        self.app.btn_back.draw(self.app.screen)

        # Panneau principal
        panel_w, panel_h = 680, 480
        panel_x = self.app.base_width // 2 - panel_w // 2
        panel_y = 95
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        blue_dark = (77, 100, 139)
        blue_light = (101, 140, 179)
        text_gold = (222, 205, 163)
        text_blue = (163, 200, 222)
        
        # Fond semi-transparent simple
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((35, 30, 25, 230))
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        
        # Deux colonnes : Joueur 1 (gauche) et Joueur 2 (droite)
        col_w = panel_w // 2 - 15
        col1_x = panel_x + 10
        col2_x = panel_x + panel_w // 2 + 5
        
        # Titre Joueur 1
        p1_title = self.app.font.render("JOUEUR 1", True, gold_light)
        p1_rect = p1_title.get_rect(centerx=col1_x + col_w // 2, top=panel_y + 12)
        self.app.screen.blit(p1_title, p1_rect)
        
        # Titre Joueur 2
        p2_title = self.app.font.render("JOUEUR 2", True, blue_light)
        p2_rect = p2_title.get_rect(centerx=col2_x + col_w // 2, top=panel_y + 12)
        self.app.screen.blit(p2_title, p2_rect)
        
        # Séparateur vertical
        sep_x = panel_x + panel_w // 2
        pygame.draw.line(self.app.screen, gold_dark, (sep_x, panel_y + 40), (sep_x, panel_y + panel_h - 60), 2)
        
        # Configuration des touches
        actions_p1 = [
            ("p1_lane1", "Lane 1"),
            ("p1_lane2", "Lane 2"),
            ("p1_lane3", "Lane 3"),
            ("p1_unit_s", "Momie"),
            ("p1_unit_m", "Dromadaire"),
            ("p1_unit_l", "Sphinx"),
            ("p1_upgrade", "Upgrade"),
        ]
        
        actions_p2 = [
            ("p2_lane1", "Lane 1"),
            ("p2_lane2", "Lane 2"),
            ("p2_lane3", "Lane 3"),
            ("p2_unit_s", "Momie"),
            ("p2_unit_m", "Dromadaire"),
            ("p2_unit_l", "Sphinx"),
            ("p2_upgrade", "Upgrade"),
        ]
        
        btn_w = 90
        btn_h = 34
        row_h = 48
        start_y = panel_y + 50
        
        self.app.keybinding_buttons = {}
        
        # Joueur 1
        for i, (action_key, label) in enumerate(actions_p1):
            y = start_y + i * row_h
            
            # Label
            label_surf = self.app.font_small.render(label, True, text_gold)
            self.app.screen.blit(label_surf, (col1_x + 15, y + 7))
            
            # Bouton avec la touche actuelle
            btn_x = col1_x + col_w - btn_w - 10
            btn_rect = pygame.Rect(btn_x, y, btn_w, btn_h)
            self.app.keybinding_buttons[action_key] = btn_rect
            
            # Couleur selon si on édite cette touche
            if self.app.keybinding_editing == action_key:
                bg_color = (90, 70, 40)
                border_color = (255, 200, 100)
                key_text = "..."
            else:
                bg_color = (55, 50, 45)
                border_color = gold_dark
                key_text = pygame.key.name(self.app.keybindings[action_key]).upper()
            
            pygame.draw.rect(self.app.screen, bg_color, btn_rect, border_radius=6)
            pygame.draw.rect(self.app.screen, border_color, btn_rect, 2, border_radius=6)
            
            key_surf = self.app.font_small.render(key_text, True, (255, 230, 180))
            key_rect = key_surf.get_rect(center=btn_rect.center)
            self.app.screen.blit(key_surf, key_rect)
        
        # Joueur 2
        for i, (action_key, label) in enumerate(actions_p2):
            y = start_y + i * row_h
            
            # Label
            label_surf = self.app.font_small.render(label, True, text_blue)
            self.app.screen.blit(label_surf, (col2_x + 15, y + 7))
            
            # Bouton avec la touche actuelle
            btn_x = col2_x + col_w - btn_w - 10
            btn_rect = pygame.Rect(btn_x, y, btn_w, btn_h)
            self.app.keybinding_buttons[action_key] = btn_rect
            
            # Couleur selon si on édite cette touche
            if self.app.keybinding_editing == action_key:
                bg_color = (40, 60, 90)
                border_color = (100, 180, 255)
                key_text = "..."
            else:
                bg_color = (45, 55, 65)
                border_color = blue_dark
                key_text = pygame.key.name(self.app.keybindings[action_key]).upper()
            
            pygame.draw.rect(self.app.screen, bg_color, btn_rect, border_radius=6)
            pygame.draw.rect(self.app.screen, border_color, btn_rect, 2, border_radius=6)
            
            key_surf = self.app.font_small.render(key_text, True, (180, 220, 255))
            key_rect = key_surf.get_rect(center=btn_rect.center)
            self.app.screen.blit(key_surf, key_rect)
        
        # Zone d'instructions / messages en bas
        msg_y = panel_y + panel_h - 45
        
        # Message d'erreur si doublon
        if hasattr(self.app, 'keybinding_error') and self.app.keybinding_error:
            error_surf = self.app.font_small.render(self.app.keybinding_error, True, (255, 100, 100))
            error_rect = error_surf.get_rect(centerx=self.app.base_width // 2, top=msg_y)
            self.app.screen.blit(error_surf, error_rect)
        elif self.app.keybinding_editing:
            instr_text = "Appuyez sur une touche... (ESC pour annuler)"
            instr_surf = self.app.font_small.render(instr_text, True, (255, 220, 100))
            instr_rect = instr_surf.get_rect(centerx=self.app.base_width // 2, top=msg_y)
            self.app.screen.blit(instr_surf, instr_rect)
        else:
            instr_text = "Cliquez sur une touche pour la modifier"
            instr_surf = self.app.font_small.render(instr_text, True, (160, 155, 145))
            instr_rect = instr_surf.get_rect(centerx=self.app.base_width // 2, top=msg_y)
            self.app.screen.blit(instr_surf, instr_rect)

    def draw_pause(self):
        """Dessine l'écran de pause."""
        overlay = pygame.Surface((self.app.base_width, self.app.base_height), pygame.SRCALPHA)
        overlay.fill((15, 12, 8, 180))
        self.app.screen.blit(overlay, (0, 0))
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)
        bg_dark = (45, 38, 30)
        
        panel_w, panel_h = 320, 390
        panel_x = self.app.base_width // 2 - panel_w // 2
        panel_y = self.app.base_height // 2 - panel_h // 2
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((bg_dark[0], bg_dark[1], bg_dark[2], 245))
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=12)
        pygame.draw.rect(self.app.screen, gold_light, (panel_x + 6, panel_y + 6, panel_w - 12, panel_h - 12), 2, border_radius=10)
        
        title_surf = self.app.font_big.render("PAUSE", True, text_gold)
        title_rect = title_surf.get_rect(centerx=self.app.base_width // 2, top=panel_y + 25)
        self.app.screen.blit(title_surf, title_rect)
        
        sub_surf = self.app.font_small.render("ESC pour reprendre", True, (150, 145, 135))
        sub_rect = sub_surf.get_rect(centerx=self.app.base_width // 2, top=panel_y + 65)
        self.app.screen.blit(sub_surf, sub_rect)
        
        sep_y = panel_y + 95
        pygame.draw.line(self.app.screen, gold_light, (panel_x + 30, sep_y), (panel_x + panel_w - 30, sep_y), 2)
        
        btn_w, btn_h = 200, 42
        btn_x = self.app.base_width // 2 - btn_w // 2
        btn_y = panel_y + 115
        btn_gap = 50
        
        self.app.btn_resume.rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        self.app.btn_pause_options.rect = pygame.Rect(btn_x, btn_y + btn_gap, btn_w, btn_h)
        self.app.btn_pause_controls.rect = pygame.Rect(btn_x, btn_y + btn_gap * 2, btn_w, btn_h)
        self.app.btn_restart.rect = pygame.Rect(btn_x, btn_y + btn_gap * 3, btn_w, btn_h)
        self.app.btn_menu.rect = pygame.Rect(btn_x, btn_y + btn_gap * 4, btn_w, btn_h)
        
        self.app.btn_resume.draw(self.app.screen)
        self.app.btn_pause_options.draw(self.app.screen)
        self.app.btn_pause_controls.draw(self.app.screen)
        self.app.btn_restart.draw(self.app.screen)
        self.app.btn_menu.draw(self.app.screen)

    def draw_game_over(self):
        """Dessine l'écran de fin de partie."""
        overlay = pygame.Surface((self.app.base_width, self.app.base_height), pygame.SRCALPHA)
        overlay.fill((15, 12, 8, 200))
        self.app.screen.blit(overlay, (0, 0))
        
        gold_dark = (139, 119, 77)
        gold_light = (179, 156, 101)
        text_gold = (222, 205, 163)
        bg_dark = (45, 38, 30)
        
        panel_w, panel_h = 420, 320
        panel_x = self.app.base_width // 2 - panel_w // 2
        panel_y = self.app.base_height // 2 - panel_h // 2 - 20
        
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((bg_dark[0], bg_dark[1], bg_dark[2], 245))
        self.app.screen.blit(panel_surf, (panel_x, panel_y))
        
        pygame.draw.rect(self.app.screen, gold_dark, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=12)
        pygame.draw.rect(self.app.screen, gold_light, (panel_x + 6, panel_y + 6, panel_w - 12, panel_h - 12), 2, border_radius=10)
        
        is_victory = self.app.game_over_text == "VICTORY"
        title_color = (100, 255, 150) if is_victory else (255, 100, 100)
        title_text = "VICTOIRE" if is_victory else "DEFAITE"
        
        title_surf = self.app.font_big.render(title_text, True, title_color)
        title_rect = title_surf.get_rect(centerx=self.app.base_width // 2, top=panel_y + 25)
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
        record_rect = record_surf.get_rect(centerx=self.app.base_width // 2, top=stats_y)
        self.app.screen.blit(record_surf, record_rect)
        
        if self.app.match_time >= self.app.best_time or self.app.enemy_kills >= self.app.best_kills:
            stats_y += 28
            new_rec = self.app.font.render("NOUVEAU RECORD!", True, (255, 220, 80))
            rec_rect = new_rec.get_rect(centerx=self.app.base_width // 2, top=stats_y)
            bg_rect = rec_rect.inflate(24, 10)
            pygame.draw.rect(self.app.screen, (80, 60, 30), bg_rect, border_radius=6)
            pygame.draw.rect(self.app.screen, gold_light, bg_rect, 2, border_radius=6)
            self.app.screen.blit(new_rec, rec_rect)

        btn_w, btn_h = 180, 45
        btn_y = panel_y + panel_h + 25
        
        self.app.btn_restart.rect = pygame.Rect(self.app.base_width // 2 - btn_w // 2, btn_y, btn_w, btn_h)
        self.app.btn_menu.rect = pygame.Rect(self.app.base_width // 2 - btn_w // 2, btn_y + btn_h + 15, btn_w, btn_h)
        
        self.app.btn_restart.draw(self.app.screen)
        self.app.btn_menu.draw(self.app.screen)
