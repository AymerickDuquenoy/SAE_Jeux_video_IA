from dataclasses import dataclass

@dataclass
class PyramidLevel:
    """
    Component PyramidLevel. Définit le niveau de la pyramide.
    
    Attributes:
        level: Niveau de la pyramide.
    """
    level: int = 1

    def __post_init__(self):
        # S'assurer que level est positif (le mettre à 1 sinon)
        # Ne pas dépasser 5
        if self.level < 1:
            self.level = 1
        elif self.level > 5:
            self.level = 5

    def __str__(self):
        return f"PyramidLevel(level={self.level})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"level": self.level}