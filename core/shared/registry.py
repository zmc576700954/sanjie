"""Component registry -- singleton that manages all registered components.

Provides registration, lookup, listing, and unregistration of CoreComponent
instances organized by ComponentType.
"""

from __future__ import annotations

from typing import Dict, List

from core.shared.base import ComponentType, CoreComponent
from core.shared.errors import ComponentNotFoundError, DuplicateComponentError


class ComponentRegistry:
    """Singleton registry for managing CoreComponent instances.

    The registry stores components by name and organizes them by type so that
    lookups by either name or type are efficient.
    """

    _instance: ComponentRegistry | None = None

    def __new__(cls) -> ComponentRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._components: Dict[str, CoreComponent] = {}
            cls._instance._by_type: Dict[ComponentType, List[str]] = {
                t: [] for t in ComponentType
            }
        return cls._instance

    def register(self, component: CoreComponent) -> None:
        """Register a component in the registry.

        Args:
            component: The CoreComponent instance to register.

        Raises:
            DuplicateComponentError: If a component with the same name already exists.
        """
        name = component.name
        if name in self._components:
            raise DuplicateComponentError(f"Component '{name}' already registered")
        self._components[name] = component
        self._by_type[component.component_type].append(name)

    def get(self, name: str) -> CoreComponent:
        """Retrieve a component by name.

        Args:
            name: The component's registered name.

        Returns:
            The CoreComponent instance.

        Raises:
            ComponentNotFoundError: If no component with the given name exists.
        """
        if name not in self._components:
            raise ComponentNotFoundError(f"Component '{name}' not found")
        return self._components[name]

    def list_by_type(self, component_type: ComponentType) -> List[CoreComponent]:
        """List all components of a given type.

        Args:
            component_type: The ComponentType to filter by.

        Returns:
            List of CoreComponent instances matching the type.
        """
        return [self._components[name] for name in self._by_type.get(component_type, [])]

    def list_all(self) -> List[CoreComponent]:
        """List all registered components.

        Returns:
            List of all CoreComponent instances.
        """
        return list(self._components.values())

    def unregister(self, name: str) -> None:
        """Remove a component from the registry.

        If the component does not exist, this is a no-op.

        Args:
            name: The component's registered name.
        """
        if name in self._components:
            component = self._components.pop(name)
            self._by_type[component.component_type].remove(name)
