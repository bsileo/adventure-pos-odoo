# -*- coding: utf-8 -*-
"""Mock provider for tests and no-key demos.

Always requests ``search_products`` with the latest user message as ``query``
when that tool is available; otherwise returns a short assistant message.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from .base import BaseProvider, ProviderResult, ToolCall


class MockProvider(BaseProvider):
    name = "mock"

    def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ProviderResult:
        user_text = ""
        for message in reversed(messages or []):
            if message.get("role") == "user":
                user_text = (message.get("content") or "").strip()
                break

        tool_names = {
            (tool.get("function") or {}).get("name")
            for tool in (tools or [])
            if tool.get("type") == "function"
        }
        if "search_products" in tool_names and user_text:
            return ProviderResult(
                content="",
                tool_calls=[
                    ToolCall(
                        id="mock_%s" % uuid.uuid4().hex[:12],
                        name="search_products",
                        arguments={"query": user_text, "limit": 12},
                    )
                ],
                provider=self.name,
                model="mock",
                input_tokens=max(1, len(user_text.split())),
                output_tokens=8,
                raw={"mock": True},
            )

        return ProviderResult(
            content=user_text
            and "Mock provider received: %s" % user_text
            or "Mock provider has no user message.",
            tool_calls=[],
            provider=self.name,
            model="mock",
            input_tokens=max(1, len(user_text.split()) or 1),
            output_tokens=12,
            raw={"mock": True, "echo": True},
        )


def parse_tool_arguments(raw) -> Dict[str, Any]:
    """Shared helper for providers that return JSON argument strings."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        return json.loads(raw)
    return dict(raw)
