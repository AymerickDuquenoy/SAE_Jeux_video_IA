import json
from pathlib import Path


class GameSave:
    def __init__(self, app):
        self.app = app
        self.save_path = Path("assets/config/save.json")
        self.best_time = 0.0
        self.best_kills = 0


    def load(self):
        if self.save_path.exists():
            data = json.loads(self.save_path.read_text())
            self.best_time = data.get("best_time", 0.0)
            self.best_kills = data.get("best_kills", 0)


    def save(self):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_path.write_text(json.dumps({
            "best_time": self.best_time,
            "best_kills": self.best_kills
        }, indent=2))