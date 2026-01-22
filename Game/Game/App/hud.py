# Game/App/hud.py
"""
HUD (Heads-Up Display) module for Antique War.
Handles in-game UI: resource display, health bars, lane selector, etc.
"""

import pygame
import esper

from Game.App.constants import (
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_MUTED,
    HUD_PANEL_X, HUD_PANEL_Y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_ALPHA,
    LANE_BTN_X, LANE_BTN_Y, LANE_BTN_WIDTH, LANE_BTN_HEIGHT, LANE_BTN_GAP,
    LANE_COUNT
)
from Game.App.ui import UIPanel, UILaneSelector

from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.health import Health
from Game.Ecs.Components.incomeRate import IncomeRate


class GameHUD:
    """
    Manages the in-game HUD display.
    """
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font,
                 font_small: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.font_small = font_small
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Main HUD panel
        self.main_panel = UIPanel(
            HUD_PANEL_X, HUD_PANEL_Y,
            HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT,
            HUD_PANEL_ALPHA
        )
        
        # Lane selector
        self.lane_selector = UILaneSelector(
            LANE_BTN_X, LANE_BTN_Y,
            LANE_BTN_WIDTH, LANE_BTN_HEIGHT,
            LANE_BTN_GAP, font_small,
            LANE_COUNT
        )
        
        # Advanced HUD panel (optional debug info)
        self.advanced_panel = UIPanel(12, 142, 640, 74, 100)
    
    def handle_event(self, event: pygame.event.Event) -> int:
        """
        Handle HUD events. Returns lane index if lane was clicked, -1 otherwise.
        """
        return self.lane_selector.handle_event(event)
    
    def set_selected_lane(self, index: int):
        """Set the selected lane index."""
        self.lane_selector.set_selected(index)
    
    def get_selected_lane(self) -> int:
        """Get the selected lane index."""
        return self.lane_selector.get_selected()
    
    def draw(self, player_pyramid_eid: int, enemy_pyramid_eid: int,
             map_name: str = "", show_advanced: bool = False,
             match_time: float = 0.0, enemy_kills: int = 0,
             zone_counts: dict = None, map_seed: int = 0):
        """
        Draw the main HUD.
        """
        # Get game state data
        try:
            wallet = esper.component_for_entity(player_pyramid_eid, Wallet)
            player_hp = esper.component_for_entity(player_pyramid_eid, Health)
            enemy_hp = esper.component_for_entity(enemy_pyramid_eid, Health)
        except Exception:
            return
        
        # Get income rate
        try:
            income = esper.component_for_entity(player_pyramid_eid, IncomeRate)
            income_txt = f"{income.rate:.1f}/s"
        except Exception:
            income_txt = "?"
        
        # Draw main panel
        self.main_panel.draw(self.screen)
        
        x = 22
        y = 20
        
        # Line 1: Money and production
        line1 = self.font.render(
            f"Coups de fouet: {int(wallet.solde)}   |   Prod: {income_txt}",
            True, COLOR_TEXT
        )
        self.screen.blit(line1, (x, y))
        y += 24
        
        # Line 2: Pyramid health
        line2 = self.font.render(
            f"Pyramide: {player_hp.hp}/{player_hp.hp_max}   |   Ennemi: {enemy_hp.hp}/{enemy_hp.hp_max}",
            True, COLOR_TEXT
        )
        self.screen.blit(line2, (x, y))
        y += 24
        
        # Line 3: Controls reminder
        line3 = self.font_small.render(
            "Z/X/C (ou W/X/C) lane   1/2/3 spawn   U upgrade   ESC pause",
            True, COLOR_TEXT_DIM
        )
        self.screen.blit(line3, (x, y))
        
        # Lane selector
        self.lane_selector.draw(self.screen)
        
        # Map name
        map_txt = self.font_small.render(f"Map: {map_name}", True, COLOR_TEXT_MUTED)
        self.screen.blit(map_txt, (22, 118))
        
        # Advanced HUD (debug info)
        if show_advanced:
            self._draw_advanced(match_time, enemy_kills, zone_counts, map_seed)
    
    def _draw_advanced(self, match_time: float, enemy_kills: int,
                       zone_counts: dict, map_seed: int):
        """Draw advanced debug information."""
        self.advanced_panel.draw(self.screen)
        
        x = 22
        y = 150
        
        z = zone_counts or {}
        l1 = self.font_small.render(
            f"Seed: {map_seed} | open={z.get('open', 0)} dusty={z.get('dusty', 0)} interdit={z.get('forbidden', 0)}",
            True, COLOR_TEXT
        )
        l2 = self.font_small.render(
            f"Temps: {match_time:.1f}s | Kills: {enemy_kills}",
            True, COLOR_TEXT
        )
        
        self.screen.blit(l1, (x, y))
        self.screen.blit(l2, (x, y + 22))


class ControlsDisplay:
    """
    Displays the controls help screen.
    """
    
    CONTROLS = [
        "Déplacement caméra : flèches",
        "Choisir la lane : Z / X / C (ou W / X / C)",
        "Lane cliquable : boutons Lane 1/2/3 en haut",
        "Spawn unités : 1 / 2 / 3",
        "Upgrade pyramide : U",
        "Pause : ESC",
    ]
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Controls panel
        self.panel = UIPanel(48, 120, self.width - 96, self.height - 190, 110)
    
    def draw(self):
        """Draw the controls help screen."""
        self.panel.draw(self.screen)
        
        x = 70
        y = 150
        
        for line in self.CONTROLS:
            surf = self.font.render(line, True, COLOR_TEXT)
            self.screen.blit(surf, (x, y))
            y += 28


class GameOverDisplay:
    """
    Displays the game over screen with stats.
    """
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font,
                 font_small: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.font_small = font_small
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Stats panel
        self.panel = UIPanel(
            self.width // 2 - 220,
            self.height // 2 - 40,
            440, 120, 120
        )
    
    def draw(self, match_time: float, enemy_kills: int,
             best_time: float, best_kills: int):
        """Draw game over stats."""
        self.panel.draw(self.screen)
        
        cx = self.width // 2
        cy = self.height // 2
        
        s1 = self.font.render(f"Temps: {match_time:.1f}s", True, COLOR_TEXT)
        s2 = self.font.render(f"Kills: {enemy_kills}", True, COLOR_TEXT)
        s3 = self.font_small.render(
            f"Record: {best_time:.1f}s | Kills record: {best_kills}",
            True, COLOR_TEXT_DIM
        )
        
        self.screen.blit(s1, (cx - 200, cy - 26))
        self.screen.blit(s2, (cx - 200, cy + 2))
        self.screen.blit(s3, (cx - 200, cy + 34))
