from abc import ABC, abstractmethod
from typing import Tuple, Any


class Driver(ABC):
    @abstractmethod
    def move_mouse(self, x: int, y: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> None:
        raise NotImplementedError

    @abstractmethod
    def type_text(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def press_key(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def screenshot(self, region: Tuple[int, int, int, int] = None) -> Any:
        raise NotImplementedError

    @abstractmethod
    def supports(self) -> dict:
        """Return driver metadata and capabilities"""
        raise NotImplementedError

#
