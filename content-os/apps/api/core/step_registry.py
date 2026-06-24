from __future__ import annotations

from typing import Any, Dict, List, Type


class StepRegistry:
    """Registry of step executors.

    Step executor classes register themselves via the ``@StepRegistry.register(step_type)``
    decorator. The pipeline engine looks up executors by step type at runtime.
    """

    _executors: Dict[str, type] = {}

    @classmethod
    def register(cls, step_type: str):
        """Decorator to register a step executor class.

        Usage::

            @StepRegistry.register("collect_sources")
            class CollectSourcesStep(StepExecutor):
                ...
        """

        def decorator(executor_class: type) -> type:
            cls._executors[step_type] = executor_class
            # Attach the step_type to the class for introspection.
            executor_class.step_type = step_type
            return executor_class

        return decorator

    @classmethod
    def get(cls, step_type: str) -> type:
        """Return the executor class for the given step type."""
        if step_type not in cls._executors:
            raise KeyError(
                f"No executor registered for step type '{step_type}'. "
                f"Available: {', '.join(sorted(cls._executors.keys()))}"
            )
        return cls._executors[step_type]

    @classmethod
    def available_steps(cls) -> List[Dict[str, Any]]:
        """Return list of available step types with their schemas."""
        result: List[Dict[str, Any]] = []
        for step_type, executor_class in sorted(cls._executors.items()):
            entry: Dict[str, Any] = {
                "step_type": step_type,
                "name": getattr(executor_class, "name", step_type),
                "description": getattr(executor_class, "description", ""),
                "required_inputs": list(getattr(executor_class, "required_inputs", []) or []),
                "produced_outputs": list(getattr(executor_class, "produced_outputs", []) or []),
            }
            result.append(entry)
        return result

    @classmethod
    def is_registered(cls, step_type: str) -> bool:
        """Check whether a step type is registered."""
        return step_type in cls._executors

    @classmethod
    def clear(cls) -> None:
        """Clear all registered executors (useful for testing)."""
        cls._executors.clear()
