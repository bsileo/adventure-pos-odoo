# -*- coding: utf-8 -*-
"""Typed capability registry for AdventurePOS AI.

Domain modules register callables the LLM may invoke. Handlers receive
``env``, validated ``args``, and a ``context`` dict; they must enforce
business rules and run as the calling user.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from odoo.exceptions import AccessError, UserError

RISK_CLASSES = ("read", "propose", "money", "inventory", "pii_write")

Handler = Callable[[Any, Dict[str, Any], Dict[str, Any]], Any]


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Handler
    risk_class: str = "read"
    feature: str = "general"
    profiles: Tuple[str, ...] = ("default",)
    group_xmlids: Tuple[str, ...] = ("adventure_ai.group_user",)
    execution_mode: str = "read"  # read | propose | auto


_REGISTRY: Dict[str, Capability] = {}


def register_capability(capability: Capability) -> Capability:
    if capability.risk_class not in RISK_CLASSES:
        raise ValueError(
            "Invalid risk_class %r for capability %s" % (capability.risk_class, capability.name)
        )
    if not capability.name:
        raise ValueError("Capability name is required")
    _REGISTRY[capability.name] = capability
    return capability


def unregister_capability(name: str) -> None:
    _REGISTRY.pop(name, None)


def clear_registry() -> None:
    """Test helper — clear all registered capabilities."""
    _REGISTRY.clear()


def get_capability(name: str) -> Optional[Capability]:
    return _REGISTRY.get(name)


def list_capabilities(profile: Optional[str] = None) -> List[Capability]:
    caps = list(_REGISTRY.values())
    if profile:
        caps = [c for c in caps if profile in c.profiles or "all" in c.profiles]
    return sorted(caps, key=lambda c: c.name)


def tools_for_provider(profile: Optional[str] = None) -> List[Dict[str, Any]]:
    """OpenAI-style tool definitions for the given profile."""
    tools = []
    for cap in list_capabilities(profile):
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": cap.name,
                    "description": cap.description,
                    "parameters": cap.parameters
                    or {"type": "object", "properties": {}, "additionalProperties": False},
                },
            }
        )
    return tools


def _user_has_groups(env, group_xmlids: Sequence[str]) -> bool:
    user = env.user
    for xmlid in group_xmlids:
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group in user.groups_id:
            return True
    return False


def assert_can_invoke(env, capability: Capability) -> None:
    if not _user_has_groups(env, capability.group_xmlids):
        raise AccessError(
            "You are not allowed to invoke AI capability '%s'." % capability.name
        )


def validate_args(capability: Capability, args: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Shallow JSON-schema validation for required properties and types."""
    args = dict(args or {})
    schema = capability.parameters or {}
    if schema.get("type") and schema.get("type") != "object":
        raise UserError("Capability %s parameters must be an object schema." % capability.name)

    properties = schema.get("properties") or {}
    required = schema.get("required") or []
    additional = schema.get("additionalProperties", True)

    missing = [key for key in required if key not in args or args[key] in (None, "")]
    if missing:
        raise UserError(
            "Capability %s missing required arguments: %s"
            % (capability.name, ", ".join(missing))
        )

    if additional is False:
        unknown = [key for key in args if key not in properties]
        if unknown:
            raise UserError(
                "Capability %s received unknown arguments: %s"
                % (capability.name, ", ".join(unknown))
            )

    for key, prop in properties.items():
        if key not in args or args[key] is None:
            continue
        expected = prop.get("type")
        value = args[key]
        if expected == "string" and not isinstance(value, str):
            args[key] = str(value)
        elif expected == "integer":
            try:
                args[key] = int(value)
            except (TypeError, ValueError) as exc:
                raise UserError(
                    "Capability %s argument %s must be an integer." % (capability.name, key)
                ) from exc
        elif expected == "number":
            try:
                args[key] = float(value)
            except (TypeError, ValueError) as exc:
                raise UserError(
                    "Capability %s argument %s must be a number." % (capability.name, key)
                ) from exc
        elif expected == "boolean" and not isinstance(value, bool):
            if isinstance(value, str):
                args[key] = value.strip().lower() in ("1", "true", "yes", "y")
            else:
                args[key] = bool(value)
        elif expected == "array" and not isinstance(value, list):
            raise UserError(
                "Capability %s argument %s must be an array." % (capability.name, key)
            )
        elif expected == "object" and not isinstance(value, dict):
            raise UserError(
                "Capability %s argument %s must be an object." % (capability.name, key)
            )
    return args


def invoke_capability(
    env,
    name: str,
    args: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Any:
    capability = get_capability(name)
    if not capability:
        raise UserError("Unknown AI capability: %s" % name)
    assert_can_invoke(env, capability)
    validated = validate_args(capability, args)
    return capability.handler(env, validated, dict(context or {}))
