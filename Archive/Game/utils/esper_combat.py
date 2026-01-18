from typing import Any

def unpack(comp: Any) -> Any:
    return comp[0] if isinstance(comp, list) else comp
