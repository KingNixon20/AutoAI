import yaml
from typing import List, Dict, Any


class Workflow:
    def __init__(self, name: str, steps: List[Dict[str, Any]] = None):
        self.name = name
        self.steps = steps or []

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "steps": self.steps}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(name=data.get("name", "unnamed"), steps=data.get("steps", []))

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)
