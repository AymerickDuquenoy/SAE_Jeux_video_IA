from dataclasses import dataclass

@dataclass
# Composant qui définit l'équipe/faction d'une entité (0=neutre, 1=joueur, 2=ennemi)
class Team:
    """Composant ECS décrivant l'appartenance d'équipe/faction.

    Attributes:
        id: Identifiant d'équipe (ex: 0 neutre, 1 joueurs, 2 ennemis).
    """
    id: int = 0