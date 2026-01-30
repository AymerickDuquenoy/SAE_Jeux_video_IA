# Game/Services/balance_config.py
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class BalanceConfig:
    """
    Classe représentant une configuration d'équilibrage chargée depuis un fichier JSON.
    Attributes:
        data: Dictionnaire contenant les données de configuration.
    """
    data: Dict[str, Any]

    # Charge une configuration d'équilibrage depuis un fichier JSON
    @classmethod
    def load(cls, path: str) -> "BalanceConfig":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"balance config introuvable: {p}")

        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(data=data)

    # Accède aux valeurs imbriquées dans la configuration via une séquence de clés
    def get(self, *keys, default=None):
        cur: Any = self.data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur
