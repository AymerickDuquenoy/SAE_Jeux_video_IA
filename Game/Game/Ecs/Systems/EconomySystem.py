# Game/Ecs/Systems/EconomySystem.py
import esper

from Game.Ecs.Components.wallet import Wallet
from Game.Ecs.Components.incomeRate import IncomeRate


class EconomySystem:
    """
    Ajoute automatiquement des "coups de fouet" au Wallet selon IncomeRate.

    IMPORTANT :
    - Esper appelle .process(dt)
    """

    # Initialise le système économique avec la pyramide joueur et revenus de base
    def __init__(self, player_pyramid_eid: int | None = None, default_income: float = 2.0):
        self.player_pyramid_eid = player_pyramid_eid
        self.default_income = float(default_income)
        self._default_ready = False

    # S'assure que la pyramide joueur a les composants Wallet et IncomeRate
    def _ensure_player_has_income(self):
        if self._default_ready or self.player_pyramid_eid is None:
            return

        eid = int(self.player_pyramid_eid)

        # Wallet
        try:
            esper.component_for_entity(eid, Wallet)
        except Exception:
            esper.add_component(eid, Wallet(solde=0.0))

        # IncomeRate
        try:
            esper.component_for_entity(eid, IncomeRate)
        except Exception:
            esper.add_component(eid, IncomeRate(rate=self.default_income))

        self._default_ready = True

    # Ajoute les revenus passifs à toutes les entités avec Wallet et IncomeRate
    def process(self, dt: float):
        self._ensure_player_has_income()

        for _eid, (wallet, income) in esper.get_components(Wallet, IncomeRate):
            wallet.solde += getattr(income, "effective_rate", income.rate) * float(dt)
            if wallet.solde < 0:
                wallet.solde = 0.0

    # bonus compat si ton World appelle system(dt) ou system(world, dt)
    # Permet d'appeler le système avec différentes signatures (compatibilité)
    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            return self.process(args[0])  # dt
        if len(args) == 2:
            return self.process(args[1])  # (world, dt)
        return self.process(kwargs.get("dt", 0.0))