import esper
from components import Health, Target, Pyramid


class DeathCleanupSystem(esper.Processor):
    def process(self, dt: float):
        for _e, tgt in esper.get_component(Target):
            if tgt.entity is None:
                continue
            if not esper.entity_exists(tgt.entity):
                tgt.entity = None
                continue
            if esper.has_component(tgt.entity, Health):
                thp = esper.component_for_entity(tgt.entity, Health)
                if thp.hp <= 0:
                    tgt.entity = None

        dead = []
        for ent, hp in esper.get_component(Health):
            if hp.hp <= 0 and not esper.has_component(ent, Pyramid):
                dead.append(ent)

        for ent in dead:
            esper.delete_entity(ent, immediate=True)
