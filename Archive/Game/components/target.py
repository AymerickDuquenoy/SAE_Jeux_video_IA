from dataclasses import dataclass
from typing import Optional

@dataclass
class Target:
    entity: Optional[int] = None
