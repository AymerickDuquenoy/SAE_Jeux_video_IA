from dataclasses import dataclass

@dataclass
class Target:
    """
    Composant Target. Définit une cible pour une entité (ex: unité attaquante).
    
    Attributs:
        entity_id: ID de l'entité cible.
        type: Type de cible (ex: "ennemy", "pyramid").
    """
    entity_id: int = None
    type: str = "entity" 

    def __post_init__(self):
        # S'assurer que entity_id est défini
        if self.entity_id is None:
            raise ValueError("Target doit avoir un entity_id défini.")