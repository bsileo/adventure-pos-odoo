# -*- coding: utf-8 -*-
"""Provider interface for AdventurePOS AI."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResult:
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    raw: Optional[Dict[str, Any]] = None


class BaseProvider:
    """Minimal chat + tools completion interface."""

    name = "base"

    def __init__(self, env):
        self.env = env

    def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ProviderResult:
        raise NotImplementedError

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Rough USD estimate; override per provider when rates are known."""
        # Default placeholder rates (USD / 1M tokens) for metering until configured.
        rates = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (2.50, 10.00),
            "mock": (0.0, 0.0),
        }
        input_rate, output_rate = rates.get(model, (1.0, 3.0))
        return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000.0
