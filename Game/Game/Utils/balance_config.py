# Game/Services/balance_config.py
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class BalanceConfig:
    data: Dict[str, Any]

    @classmethod
    def load(cls, path: str) -> "BalanceConfig":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"balance config introuvable: {p}")

        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(data=data)

    def get(self, *keys, default=None):
        cur: Any = self.data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur
