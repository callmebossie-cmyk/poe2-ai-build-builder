from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

from .database import connect


class GraphError(ValueError):
    """Base error for invalid passive graph operations."""


class NodeNotFoundError(GraphError):
    """Raised when a requested node does not exist."""


class PathNotFoundError(GraphError):
    """Raised when two known nodes are disconnected under current rules."""


@dataclass(frozen=True)
class PassivePath:
    nodes: tuple[str, ...]

    @property
    def point_cost(self) -> int:
        """Allocation cost when the first node is an already-owned class start."""
        return max(0, len(self.nodes) - 1)


class PassiveGraph:
    def __init__(
        self,
        adjacency: dict[str, set[str]],
        names: dict[str, str | None],
        class_starts: dict[str, str],
    ) -> None:
        self.adjacency = adjacency
        self.names = names
        self.class_starts = class_starts

    @classmethod
    def from_database(
        cls,
        database_path: Path,
        *,
        allowed_ascendancy: str | None = None,
    ) -> "PassiveGraph":
        db = connect(database_path)
        try:
            node_rows = db.execute("SELECT id,name,ascendancy_id FROM passive_nodes").fetchall()
            names = {row["id"]: row["name"] for row in node_rows if row["id"] != "root"}
            ascendancies = {row["id"]: row["ascendancy_id"] for row in node_rows}
            adjacency = {node_id: set() for node_id in names}
            for edge in db.execute("SELECT from_node,to_node FROM passive_edges"):
                start, end = edge["from_node"], edge["to_node"]
                if start == "root" or end == "root":
                    continue
                if start not in adjacency or end not in adjacency:
                    continue
                if ascendancies[start] not in (None, allowed_ascendancy):
                    continue
                if ascendancies[end] not in (None, allowed_ascendancy):
                    continue
                adjacency[start].add(end)
                adjacency[end].add(start)
            class_starts = {
                row["class_name"]: row["node_id"]
                for row in db.execute("SELECT class_name,node_id FROM class_starts")
            }
        finally:
            db.close()
        return cls(adjacency, names, class_starts)

    def class_start(self, class_name: str) -> str:
        try:
            return self.class_starts[class_name]
        except KeyError as error:
            available = ", ".join(sorted(self.class_starts))
            raise NodeNotFoundError(f"Unknown class {class_name!r}; available: {available}") from error

    def shortest_path(self, start: str, target: str) -> PassivePath:
        for node_id in (start, target):
            if node_id not in self.adjacency:
                raise NodeNotFoundError(f"Passive node does not exist: {node_id}")
        queue = deque([start])
        previous: dict[str, str | None] = {start: None}
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbour in sorted(self.adjacency[current]):
                if neighbour not in previous:
                    previous[neighbour] = current
                    queue.append(neighbour)
        if target not in previous:
            raise PathNotFoundError(f"No allocatable passive path from {start} to {target}")
        path = []
        current: str | None = target
        while current is not None:
            path.append(current)
            current = previous[current]
        return PassivePath(tuple(reversed(path)))

    def component_size(self, start: str) -> int:
        if start not in self.adjacency:
            raise NodeNotFoundError(f"Passive node does not exist: {start}")
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbour in self.adjacency[current]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(neighbour)
        return len(visited)

    def find_nodes(self, text: str) -> list[tuple[str, str]]:
        needle = text.casefold()
        return sorted(
            (node_id, name)
            for node_id, name in self.names.items()
            if name and needle in name.casefold()
        )
