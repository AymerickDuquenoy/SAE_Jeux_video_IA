import esper
import pygame
from components import UIInput, Wallet, Spawner, UpgradeRequest
from game.unit_stats import UNIT_STATS


class UIClickSystem(esper.Processor):
    def __init__(self, screen: pygame.Surface, player_entity: int):
        super().__init__()
        self.screen = screen
        self.player_entity = player_entity

        self.btn_h = 44
        self.btn_w = 160
        self.pad = 10

        self.buttons = [
            ("buy_momie", "momie"),
            ("buy_dromadaire", "dromadaire"),
            ("buy_sphinx", "sphinx"),
            ("upgrade", None),
        ]

    def get_button_rects(self):
        rects = {}
        y = self.screen.get_height() - self.btn_h - self.pad
        x = self.pad
        for bid, _payload in self.buttons:
            rects[bid] = pygame.Rect(x, y, self.btn_w, self.btn_h)
            x += self.btn_w + self.pad
        return rects

    def _try_buy_and_queue(self, unit_type: str):
        wallet = esper.component_for_entity(self.player_entity, Wallet)
        spawner = esper.component_for_entity(self.player_entity, Spawner)

        cost = UNIT_STATS[unit_type]["cost"]
        if wallet.amount >= cost:
            wallet.amount -= cost
            spawner.queue.append(unit_type)
            print(f"[UI] Bought {unit_type} for {cost} 𓍯 (wallet={wallet.amount:.1f})")
        else:
            print(f"[UI] Not enough 𓍯 for {unit_type} (need {cost}, have {wallet.amount:.1f})")

    def process(self, dt: float):
        rects = self.get_button_rects()

        ui = None
        for _e, u in esper.get_component(UIInput):
            ui = u
            break
        if ui is None:
            return

        clicks = list(ui.mouse_clicks)
        ui.mouse_clicks.clear()

        for cx, cy in clicks:
            for bid, payload in self.buttons:
                if rects[bid].collidepoint((cx, cy)):
                    if bid == "upgrade":
                        if not esper.has_component(self.player_entity, UpgradeRequest):
                            esper.add_component(self.player_entity, UpgradeRequest())
                        print("[UI] Upgrade requested")
                    else:
                        self._try_buy_and_queue(payload)
                    break
