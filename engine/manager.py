from typing import List, Optional
import importlib


class DriverManager:
    """Selects and manages input drivers with fallbacks.

    Strategy: read a comma-separated priority list and return the first available driver.
    """

    def __init__(self, priority: Optional[List[str]] = None):
        # default priority
        if priority is None:
            priority = ["pyautogui", "xdotool", "ydotool"]
        self.priority = priority
        self._drivers = {}

    def discover(self):
        """Attempt to import known driver modules and instantiate them lazily."""
        # Known mapping from name -> module path -> class name
        mapping = {
            "pyautogui": ("engine.drivers.pyautogui_driver", "PyAutoGuiDriver"),
        }

        for name, (modpath, clsname) in mapping.items():
            try:
                mod = importlib.import_module(modpath)
                cls = getattr(mod, clsname)
                self._drivers[name] = cls()
            except Exception:
                # driver not available or failed to initialize
                continue

    def get_driver(self):
        """Return first available driver by priority, or None."""
        if not self._drivers:
            self.discover()

        for name in self.priority:
            drv = self._drivers.get(name)
            if drv:
                return drv
        return None

    def set_priority(self, priority_list: List[str]):
        self.priority = priority_list

#
