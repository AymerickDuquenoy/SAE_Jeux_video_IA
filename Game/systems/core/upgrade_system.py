import esper
from components import Pyramid, Team, Health, Wallet, UpgradeRequest, PyramidLevel

try:
    from components import IncomeMultiplier
    HAS_MULT = True
except Exception:
    HAS_MULT = False


class UpgradeSystem(esper.Processor):
    MAX_LEVEL = 5
    HP_PER_LEVEL = 50
    INCOME_MULT_PER_LEVEL = 1.25

    def process(self, dt: float):
        reqs = list(esper.get_component(UpgradeRequest))
        if not reqs:
            return

        for req_ent, _req in reqs:
            if not (esper.has_component(req_ent, Team) and esper.has_component(req_ent, Wallet)):
                esper.remove_component(req_ent, UpgradeRequest)
                continue

            team = esper.component_for_entity(req_ent, Team)
            wallet = esper.component_for_entity(req_ent, Wallet)

            pyr_ent = None
            for p_ent, (_pyr, p_team, _hp) in esper.get_components(Pyramid, Team, Health):
                if p_team.id == team.id:
                    pyr_ent = p_ent
                    break

            if pyr_ent is None:
                esper.remove_component(req_ent, UpgradeRequest)
                continue

            if not esper.has_component(pyr_ent, PyramidLevel):
                esper.add_component(pyr_ent, PyramidLevel(level=0))

            lvl = esper.component_for_entity(pyr_ent, PyramidLevel)
            hp = esper.component_for_entity(pyr_ent, Health)

            if lvl.level >= self.MAX_LEVEL:
                esper.remove_component(req_ent, UpgradeRequest)
                continue

            cost = 100 + 25 * lvl.level
            if wallet.amount < cost:
                esper.remove_component(req_ent, UpgradeRequest)
                continue

            wallet.amount -= cost
            lvl.level += 1
            hp.max_hp += self.HP_PER_LEVEL
            hp.hp = min(hp.max_hp, hp.hp + self.HP_PER_LEVEL)

            if HAS_MULT:
                if not esper.has_component(pyr_ent, IncomeMultiplier):
                    esper.add_component(pyr_ent, IncomeMultiplier(mult=1.0))
                mult = esper.component_for_entity(pyr_ent, IncomeMultiplier)
                mult.mult *= self.INCOME_MULT_PER_LEVEL

            print(f"[UPGRADE] Team {team.id} pyramid -> level {lvl.level} (cost {cost})")
            esper.remove_component(req_ent, UpgradeRequest)
