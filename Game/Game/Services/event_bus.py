# Game/Services/event_bus.py
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._subs = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[..., Any]):
        self._subs[event_name].append(callback)

    def emit(self, event_name: str, **payload):
        for cb in self._subs.get(event_name, []):
            cb(**payload)

    def clear(self):
        self._subs.clear()
