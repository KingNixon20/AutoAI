import pyautogui
from ..driver import Driver


class PyAutoGuiDriver(Driver):
    def __init__(self):
        pyautogui.FAILSAFE = True

    def move_mouse(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)

    def click(self, x: int, y: int, button: str = "left") -> None:
        pyautogui.click(x=x, y=y, button=button)

    def type_text(self, text: str) -> None:
        pyautogui.typewrite(text)

    def press_key(self, key: str) -> None:
        pyautogui.press(key)

    def screenshot(self, region=None):
        if region:
            return pyautogui.screenshot(region=region)
        return pyautogui.screenshot()

    def supports(self) -> dict:
        return {"name": "pyautogui", "display": "generic", "available": True}

#
