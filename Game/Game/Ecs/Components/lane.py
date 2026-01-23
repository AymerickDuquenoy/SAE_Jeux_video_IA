from dataclasses import dataclass

@dataclass
class Lane:
    """
    Stocke la lane assignée à une unité (0, 1, ou 2).
    Utilisé pour le ciblage : les unités ne ciblent que sur leur lane.
    """
    index: int = 1  # 0=haut, 1=milieu, 2=bas
    y_position: float = 0.0  # Position Y de la lane
