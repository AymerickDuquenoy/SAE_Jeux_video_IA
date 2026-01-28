# Game/Services/event_bus.py
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    """
    Classe gérant un bus d'événements simple.
    Attributes:
        _subs: Dictionnaire mappant les noms d'événements aux listes de callbacks.
    """
    def __init__(self):
        self._subs = defaultdict(list)

    # Abonne un callback à un événement donné
    def subscribe(self, event_name: str, callback: Callable[..., Any]):
        self._subs[event_name].append(callback)

    # Émet un événement avec des données optionnelles
    def emit(self, event_name: str, **payload):
        for cb in self._subs.get(event_name, []):
            cb(**payload)

    # Désabonne un callback d'un événement donné
    def clear(self):
        self._subs.clear()
