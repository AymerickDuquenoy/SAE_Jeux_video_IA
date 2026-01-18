import esper

from Game.Ecs.Components.health import Health
from Game.Ecs.Components.lifetime import Lifetime


class CleanupSystem(esper.Processor):
    """
    - Supprime les entités mortes (sauf celles protégées : pyramides)
    - Gère aussi Lifetime.ttl si utilisé
    """

    def __init__(self, *, protected_entities: set[int] | None = None):
        super().__init__()
        self.protected = set(protected_entities or set())

    def process(self, dt: float):
        to_delete = []

        # TTL
        for eid, (lt,) in esper.get_components(Lifetime):
            lt.tick(dt)
            if lt.expired and eid not in self.protected:
                to_delete.append(eid)

        # morts
        for eid, (hp,) in esper.get_components(Health):
            if eid in self.protected:
                continue
            if hp.is_dead:
                to_delete.append(eid)

        # suppression
        for eid in set(to_delete):
            try:
                esper.delete_entity(eid, immediate=True)
            except Exception:
                pass
