from dataclasses import dataclass
from enum import IntFlag, auto

class EventFlag(IntFlag):
    """Flags d'effets possibles (bitmask)."""
    NONE          = 0
    DAMAGE        = auto()  # ex: nuée de sauterelles (dégâts globaux)
    SLOW          = auto()  # ex: impact temporaire (ralentissement générique)
    STUN          = auto()
    HEAL          = auto()
    BUFF          = auto()
    DEBUFF        = auto()
    ECONOMY_BUFF  = auto()  # ex: livraison de fouets (x1.25 temporaire) côté joueur

# Par défaut, une unité standard peut être affectée par la plupart des effets
DEFAULT_UNIT_FLAGS = (
    EventFlag.DAMAGE
    | EventFlag.SLOW
    | EventFlag.BUFF
    | EventFlag.DEBUFF
)

@dataclass
class AffectableByEvent:
    """
    Indique à quels événements/effets l'entité réagit.

    Args:
        flags: combinaison de EventFlag (bitmask).
    """
    flags: EventFlag = DEFAULT_UNIT_FLAGS

    def accepts(self, flag: EventFlag) -> bool:
        """Vrai si l'entité accepte l'effet 'flag'."""
        return bool(self.flags & flag)

    def enable(self, flag: EventFlag) -> None:
        """Autorise dynamiquement un effet."""
        self.flags |= flag

    def disable(self, flag: EventFlag) -> None:
        """Désactive dynamiquement un effet."""
        self.flags &= ~flag

    def to_int(self) -> int:
        return int(self.flags)

    def to_dict(self):
        return {"flags": int(self.flags)}
