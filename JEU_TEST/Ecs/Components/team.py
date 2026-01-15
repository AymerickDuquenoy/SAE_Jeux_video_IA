from dataclasses import dataclass

@dataclass
class Team:
    """Composant ECS décrivant l'appartenance d'équipe/faction.

    Attributes:
        id: Identifiant d'équipe (ex: 0 neutre, 1 joueurs, 2 ennemis).
    """
    id: int = 0
