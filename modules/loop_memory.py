import json
from typing import List

class LoopMemory:
    """Simple persistent log for recording each run (query and confidence)."""
    def __init__(self, path: str = "loop_log.json"):
        self.path = path
        self.log: List[dict] = []

    def append(self, entry: dict):
        self.log.append(entry)
        self.save()

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.log, f, indent=2)

    def load(self) -> List[dict]:
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
