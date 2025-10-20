import esper
from typing import Callable


class World:
    def __init__(self):
        self._systems = []

    def add_system(self, system_func: Callable, priority: int = 0):
        self._systems.append((priority, system_func))
        self._systems.sort(key=lambda x: x[0])

    def create_entity(self, *components):
        return esper.create_entity(*components)

    def delete_entity(self, entity_id: int):
        esper.delete_entity(entity_id, immediate=True)

    def get_component(self, component_type):
        return esper.get_component(component_type)

    def get_components(self, *component_types):
        return esper.get_components(*component_types)

    def process(self, dt: float):
        for _, system in self._systems:
            system(self._world, dt)



"""
# --- TESTS MANUELS ---
from Game.Ecs.Components.grid_position import GridPosition as grid_position
if __name__ == "__main__":
    print("=== Test 1 : création et suppression d'entité ===")
    world = World()
    eid = world.create_entity(grid_position(10, 20))
    eid = world.create_entity(grid_position(5, 20))
    if len(world.get_component(grid_position)) == 2:
        print("✅ Entité créée avec succès")
    else:
        print("❌ Erreur : entité non créée")

    world.delete_entity(1)
    world.delete_entity(2)
    if len(world.get_component(grid_position)) == 0:
        print("✅ Entité supprimée avec succès")
    else:
        print("❌ Erreur : entité non supprimée")
"""