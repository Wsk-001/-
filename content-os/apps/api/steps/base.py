from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.pipeline_engine import StepContext, StepResult


class StepExecutor(ABC):
    """Abstract base class for all step executors.

    Subclasses must set the class-level attributes ``name`` and ``description``
    and implement :meth:`execute`.
    """

    step_type: str = ""
    name: str = ""
    description: str = ""
    required_inputs: list[str] = []
    produced_outputs: list[str] = []

    @abstractmethod
    async def execute(self, ctx: StepContext) -> StepResult:
        """Execute the step and return a :class:`StepResult`.

        Args:
            ctx: The step context containing task id, config, and accumulated
                artifacts from upstream steps.
        """
        ...
