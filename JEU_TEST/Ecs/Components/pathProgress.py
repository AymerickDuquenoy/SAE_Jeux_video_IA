from dataclasses import dataclass

@dataclass
class PathProgress:
    """Composant ECS décrivant la progression d’une entité le long de son chemin.

    Attributes:
        index: Indice actuel dans la liste des noeuds du Path.
               Commence à 0 et s’incrémente lorsque l’unité atteint un nœud.
    """
    index: int = 0
