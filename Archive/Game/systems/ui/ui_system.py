import pygame
import esper
from components import Wallet, UIInput


class UISystem(esper.Processor):
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, player_entity: int):
        super().__init__()
        self.screen = screen
        self.font = font
        self.player_entity = player_entity

        self.btn_h = 44
        self.btn_w = 160
        self.pad = 10

        self.buttons = [
            ("buy_momie", "Momie"),
            ("buy_dromadaire", "Dromadaire"),
            ("buy_sphinx", "Sphinx"),
            ("upgrade", "Upgrade"),
        ]

    def get_button_rects(self):
        rects = {}
        y = self.screen.get_height() - self.btn_h - self.pad
        x = self.pad
        for bid, _label in self.buttons:
            rects[bid] = pygame.Rect(x, y, self.btn_w, self.btn_h)
            x += self.btn_w + self.pad
        return rects

    def process(self, dt: float):
        rects = self.get_button_rects()

        wallet_amount = esper.component_for_entity(self.player_entity, Wallet).amount
        txt = self.font.render(f"𓍯 {wallet_amount:.1f}", True, (240, 240, 240))
        self.screen.blit(txt, (10, 10))

        mouse_pos = (0, 0)
        for _e, ui in esper.get_component(UIInput):
            mouse_pos = ui.mouse_pos
            break

        for bid, label in self.buttons:
            r = rects[bid]
            hovered = r.collidepoint(mouse_pos)

            bg = (70, 70, 70) if not hovered else (95, 95, 95)
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            pygame.draw.rect(self.screen, (20, 20, 20), r, width=2, border_radius=8)

            t = self.font.render(label, True, (240, 240, 240))
            self.screen.blit(t, (r.x + 10, r.y + 12))