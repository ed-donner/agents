import abc

from typing import Literal


class InstructionsModel(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the instruction model."""
        pass

    @property
    @abc.abstractmethod
    def instructions(self) -> str:
        """Return the instructions for the model."""
        pass

    @property
    @abc.abstractmethod
    def handoff_description(self) -> str:
        """Return the handoff description for the model."""
        pass

    @property
    @abc.abstractmethod
    def model(self) -> Literal["gpt-4o-mini", "gpt-4o"]:
        """Return the model type."""
        pass
