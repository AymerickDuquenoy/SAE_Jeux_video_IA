import esper
from components import Wallet, IncomeRate


class EconomySystem(esper.Processor):
    def __init__(self):
        super().__init__()
        self._dbg = 0.0

    def process(self, dt: float):
        if dt <= 0:
            return

        # update economy
        matched = 0
        for _ent, (w, inc) in esper.get_components(Wallet, IncomeRate):
            w.amount += inc.per_second * dt
            matched += 1

        # debug once/sec
        self._dbg += dt
        if self._dbg >= 1.0:
            self._dbg = 0.0
            print(f"[ECO] matched Wallet+IncomeRate = {matched}")
