from dataclasses import dataclass

@dataclass
class RandomEventTag:
    """
    Tag pour marquer une entité/objet issu d'un événement aléatoire.
    Exemples de tag: 'sandstorm', 'locust_swarm', 'whip_delivery'.
    """
    tag: str = "random_event"

    def to_dict(self):
        return {"tag": self.tag}
