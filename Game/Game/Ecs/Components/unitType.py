# Game/Ecs/Components/unitType.py
from dataclasses import dataclass

@dataclass
class UnitType:
    """
    Permet d'afficher le type (S/M/L) et de faire du visuel plus propre.
    """
    key: str  # "S" / "M" / "L"
