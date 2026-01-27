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

    # Active le contexte du monde pour qu'Esper sache sur quel monde travailler
    def _activate(self):
        esper.switch_world(self.name)

    # Ajoute un système (processor) au monde avec une priorité d'exécution
    def add_system(self, processor, priority: int = 0):
        self._activate()
        esper.add_processor(processor, priority=priority)

    # Crée une nouvelle entité avec les composants fournis et retourne son ID
    def create_entity(self, *components):
        self._activate()
        return esper.create_entity(*components)

    # Supprime une entité du monde (immediate=True pour suppression instantanée)
    def delete_entity(self, entity_id: int, immediate: bool = False):
        self._activate()
        esper.delete_entity(entity_id, immediate=immediate)

    # Récupère toutes les entités ayant un composant spécifique
    def get_component(self, component_type):
        self._activate()
        return esper.get_component(component_type)

    # Récupère toutes les entités ayant tous les composants spécifiés
    def get_components(self, *component_types):
        self._activate()
        return esper.get_components(*component_types)

    # Récupère un composant spécifique d'une entité donnée
    def component_for_entity(self, entity_id: int, component_type):
        self._activate()
        return esper.component_for_entity(entity_id, component_type)

    # Vérifie si une entité possède un composant spécifique
    def has_component(self, entity_id: int, component_type):
        self._activate()
        return esper.has_component(entity_id, component_type)

    # Ajoute un composant à une entité existante
    def add_component(self, entity_id: int, component):
        self._activate()
        esper.add_component(entity_id, component)

    # Retire un composant d'une entité et le retourne
    def remove_component(self, entity_id: int, component_type):
        self._activate()
        return esper.remove_component(entity_id, component_type)

    # Exécute tous les systèmes du monde avec le delta time fourni
    def process(self, dt: float):
        self._activate()
        esper.process(dt)