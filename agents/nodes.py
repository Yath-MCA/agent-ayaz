"""Distributed Node Registry — Phase 13 stub.

Nodes self-register with the orchestrator. In this version the registry
is in-memory. A persistent backend (Redis/DB) can be swapped in later.
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentNode:
    node_id: str
    host: str
    port: int
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    capabilities: list[str] = field(default_factory=list)

    def is_alive(self, timeout: int = 30) -> bool:
        return (time.time() - self.last_heartbeat) < timeout

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
            "alive": self.is_alive(),
            "capabilities": self.capabilities,
        }


class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: dict[str, AgentNode] = {}

    def register(self, node_id: str, host: str, port: int, capabilities: Optional[list[str]] = None) -> AgentNode:
        node = AgentNode(node_id=node_id, host=host, port=port, capabilities=capabilities or [])
        self._nodes[node_id] = node
        return node

    def heartbeat(self, node_id: str) -> bool:
        node = self._nodes.get(node_id)
        if not node:
            return False
        node.last_heartbeat = time.time()
        return True

    def deregister(self, node_id: str) -> bool:
        return self._nodes.pop(node_id, None) is not None

    def alive_nodes(self) -> list[AgentNode]:
        return [n for n in self._nodes.values() if n.is_alive()]

    def all_nodes(self) -> list[AgentNode]:
        return list(self._nodes.values())


# Global singleton
node_registry = NodeRegistry()
