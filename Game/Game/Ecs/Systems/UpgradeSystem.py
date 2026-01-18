# Game/Ecs/Systems/UpgradeSystem.py
import math
import esper

from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.incomeRate import IncomeRate
from Game.Ecs.Components.pyramidLevel import PyramidLevel
from Game.Ecs.Components.upgradeable import Upgradeable
from Game.Ecs.Components.health import Health


class UpgradeSystem:
    """
    Upgrade pyramide (niveau 1->5) :
    - +50 HP max par niveau
    - production (IncomeRate) x1.25 par niveau
    - coût augmente à chaque upgrade

    IMPORTANT :
    - Esper appelle .process(dt)
    """

    def __init__(
        self,
        player_pyramid_eid: int,
        max_level: int = 5,
        hp_bonus_per_level: int = 50,
        prod_multiplier: float = 1.25,
        cost_multiplier: float = 1.6,
        base_cost: float = 100.0,
    ):
        self.player_pyramid_eid = int(player_pyramid_eid)

        self.max_level = int(max_level)
        self.hp_bonus_per_level = int(hp_bonus_per_level)
        self.prod_multiplier = float(prod_multiplier)
        self.cost_multiplier = float(cost_multiplier)
        self.base_cost = float(base_cost)

        self._requested = False
        self.last_message = ""

    def request_upgrade(self):
        self._requested = True

    def _ensure_components(self):
        eid = self.player_pyramid_eid

        # Wallet
        try:
            esper.component_for_entity(eid, Wallet)
        except Exception:
            esper.add_component(eid, Wallet(solde=0.0))

        # IncomeRate
        try:
            esper.component_for_entity(eid, IncomeRate)
        except Exception:
            esper.add_component(eid, IncomeRate(rate=2.0))

        # PyramidLevel
        try:
            esper.component_for_entity(eid, PyramidLevel)
        except Exception:
            esper.add_component(eid, PyramidLevel(level=1))

        # Upgradeable
        try:
            esper.component_for_entity(eid, Upgradeable)
        except Exception:
            esper.add_component(eid, Upgradeable(upgrade_cost=self.base_cost))

    def process(self, dt: float):
        if not self._requested:
            return

        self._requested = False
        self._ensure_components()

        eid = self.player_pyramid_eid

        wallet = esper.component_for_entity(eid, Wallet)
        level = esper.component_for_entity(eid, PyramidLevel)
        upg = esper.component_for_entity(eid, Upgradeable)
        income = esper.component_for_entity(eid, IncomeRate)

        if level.level >= self.max_level:
            self.last_message = "Pyramide déjà au niveau max."
            return

        cost = float(upg.upgrade_cost)
        if wallet.solde < cost:
            self.last_message = f"Pas assez de coups de fouet (besoin: {int(cost)})."
            return

        # payer
        wallet.solde -= cost
        if wallet.solde < 0:
            wallet.solde = 0.0

        # upgrade niveau
        level.level = min(self.max_level, level.level + 1)

        # HP +50 (si Health existe)
        try:
            hp = esper.component_for_entity(eid, Health)
            hp.hp_max += self.hp_bonus_per_level
            hp.hp = min(hp.hp + self.hp_bonus_per_level, hp.hp_max)
        except Exception:
            pass

        # production x1.25
        income.rate = float(income.rate) * self.prod_multiplier

        # coût suivant
        upg.upgrade_cost = float(math.ceil(cost * self.cost_multiplier))

        self.last_message = f"Upgrade pyramide -> niveau {level.level}."

    # bonus : permet aussi de fonctionner si ton World appelle system(dt) ou system(world, dt)
    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            return self.process(args[0])  # dt
        if len(args) == 2:
            return self.process(args[1])  # (world, dt)
        return self.process(kwargs.get("dt", 0.0))
