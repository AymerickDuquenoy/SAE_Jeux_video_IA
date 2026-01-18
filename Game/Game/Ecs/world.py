# Game/Ecs/world.py
import esper


class World:
    """
    Wrapper autour d'Esper 3.x (World context global).
    On isole notre "World" en utilisant esper.switch_world(name).
    """

    def __init__(self, name: str = "game"):
        self.name = name
        self._activate()
        esper.clear_database()

    def _activate(self):
        esper.switch_world(self.name)

    def add_system(self, processor, priority: int = 0):
        self._activate()
        esper.add_processor(processor, priority=priority)

    def create_entity(self, *components):
        self._activate()
        return esper.create_entity(*components)

    def delete_entity(self, entity_id: int, immediate: bool = False):
        self._activate()
        esper.delete_entity(entity_id, immediate=immediate)

    def get_component(self, component_type):
        self._activate()
        return esper.get_component(component_type)

    def get_components(self, *component_types):
        self._activate()
        return esper.get_components(*component_types)

    def component_for_entity(self, entity_id: int, component_type):
        self._activate()
        return esper.component_for_entity(entity_id, component_type)

    def has_component(self, entity_id: int, component_type):
        self._activate()
        return esper.has_component(entity_id, component_type)

    def add_component(self, entity_id: int, component):
        self._activate()
        esper.add_component(entity_id, component)

    def remove_component(self, entity_id: int, component_type):
        self._activate()
        return esper.remove_component(entity_id, component_type)

    def process(self, dt: float):
        self._activate()
        esper.process(dt)
