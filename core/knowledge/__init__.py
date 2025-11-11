"""Knowledge node registry and helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


@dataclass(frozen=True)
class KnowledgeNode:
    id: str
    category: str
    title: str
    before: str
    after: str
    explanation: str | None = None


class KnowledgeRegistry:
    """Loads YAML rule files from category directories and supports matching."""

    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path(__file__).resolve().parent
        self.nodes: Dict[str, KnowledgeNode] = {}
        self._load_all()

    def match(self, before: str, after: str) -> Optional[KnowledgeNode]:
        key = f"{before.strip()}::{after.strip()}"
        return self.nodes.get(key)

    def _load_all(self) -> None:
        for path in self._iter_rule_files():
            data = self._load_file(path)
            if not isinstance(data, list):
                continue
            for entry in data:
                self._register_rule(entry, path)

    def _load_file(self, path: Path):
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        if suffix == ".json":
            return json.loads(text)
        if suffix in {".yml", ".yaml"}:
            if yaml is None:
                raise RuntimeError("PyYAML is required to load YAML knowledge files.")
            return yaml.safe_load(text)
        return []

    def _iter_rule_files(self) -> Iterable[Path]:
        for yml in self.base_path.rglob("*.yml"):
            yield yml
        for yaml_path in self.base_path.rglob("*.yaml"):
            yield yaml_path
        for json_path in self.base_path.rglob("*.json"):
            yield json_path

    def _register_rule(self, entry: dict, path: Path) -> None:
        node_id = entry.get("id")
        before = entry.get("pattern", {}).get("before")
        after = entry.get("pattern", {}).get("after")
        if not node_id or not before or not after:
            return
        key = f"{before.strip()}::{after.strip()}"
        self.nodes[key] = KnowledgeNode(
            id=node_id,
            category=entry.get("category", path.parent.name),
            title=entry.get("title", ""),
            before=before,
            after=after,
            explanation=entry.get("explanation"),
        )
