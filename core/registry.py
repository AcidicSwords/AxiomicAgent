from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict


@dataclass
class ComponentRegistry:
    adapters: Dict[str, Callable] = field(default_factory=dict)
    reporters: Dict[str, Callable] = field(default_factory=dict)

    def register_adapter(self, name: str, factory: Callable):
        self.adapters[name] = factory
        return factory

    def register_reporter(self, name: str, factory: Callable):
        self.reporters[name] = factory
        return factory


REGISTRY = ComponentRegistry()
REG = REGISTRY  # Backwards compatibility for legacy imports


def register_adapter(name: str):
    def decorator(cls):
        REGISTRY.register_adapter(name, cls)
        return cls

    return decorator


def register_reporter(name: str):
    def decorator(cls):
        REGISTRY.register_reporter(name, cls)
        return cls

    return decorator

def register(category: str, name: str):
    def decorator(cls):
        return cls

    return decorator
