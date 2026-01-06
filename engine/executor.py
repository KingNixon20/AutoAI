import threading
import time
import logging
from typing import Callable, Optional
import pathlib

try:
    import pyautogui
except Exception:
    pyautogui = None

from .manager import DriverManager

log = logging.getLogger("autoai.executor")


class WorkflowExecutor:
    def __init__(self, driver_manager: Optional[DriverManager] = None):
        self.driver_manager = driver_manager or DriverManager()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self, workflow, dry_run: bool = False, on_update: Optional[Callable[[str], None]] = None, on_finished: Optional[Callable[[bool, str], None]] = None):
        """Run workflow in background thread.

        on_update(message) will be called for progress messages.
        on_finished(success: bool, message: str) will be called when done.
        """
        thread = threading.Thread(target=self._run, args=(workflow, dry_run, on_update, on_finished), daemon=True)
        thread.start()
        return thread

    def _run(self, workflow, dry_run, on_update, on_finished):
        self._stop = False
        drv = None
        try:
            drv = self.driver_manager.get_driver()
            if on_update:
                on_update(f"Selected driver: {getattr(drv, '__class__', type(drv))}")

            steps = getattr(workflow, "steps", [])
            for idx, step in enumerate(steps, start=1):
                if self._stop:
                    if on_update:
                        on_update("Execution stopped")
                    if on_finished:
                        on_finished(False, "stopped")
                    return

                stype = step.get("type")
                params = step.get("params", {})
                if on_update:
                    on_update(f"Step {idx}/{len(steps)}: {stype} {params}")

                try:
                    self._execute_step(stype, params, drv, dry_run)
                except Exception as e:
                    log.exception("Step failed")
                    if on_update:
                        on_update(f"Step failed: {e}")
                    if on_finished:
                        on_finished(False, str(e))
                    return

            if on_update:
                on_update("Workflow completed")
            if on_finished:
                on_finished(True, "completed")

        except Exception as e:
            log.exception("Executor error")
            if on_finished:
                on_finished(False, str(e))

    def _execute_step(self, stype: str, params: dict, driver, dry_run: bool):
        st = stype.lower()
        if st in ("delay",):
            seconds = float(params.get("seconds", 1.0))
            if dry_run:
                log.info(f"[dry] Delay {seconds}s")
                time.sleep(min(seconds, 0.1))
            else:
                time.sleep(seconds)

        elif st in ("typetext", "type_text"):
            text = params.get("text", "")
            if dry_run:
                log.info(f"[dry] TypeText: {text}")
            else:
                if driver:
                    driver.type_text(text)
                elif pyautogui:
                    pyautogui.typewrite(text)

        elif st in ("keypress", "key_press"):
            key = params.get("key", "")
            if dry_run:
                log.info(f"[dry] KeyPress: {key}")
            else:
                if driver:
                    driver.press_key(key)
                elif pyautogui:
                    pyautogui.press(key)

        elif st in ("findandclick", "find_and_click", "findclick"):
            class_name = params.get("class") or params.get("class_name")
            retries = int(params.get("retries", 3))
            if dry_run:
                log.info(f"[dry] FindAndClick class={class_name} retries={retries}")
                time.sleep(0.1)
                return

            # attempt to locate template image in project classes
            found = False
            # attempt to locate image inside './projects/*/classes/<class_name>/*.png'
            projects_root = pathlib.Path.cwd() / "projects"
            if projects_root.exists():
                for proj in projects_root.iterdir():
                    if not proj.is_dir():
                        continue
                    template = proj / "classes" / class_name
                    if template.exists():
                        imgs = list(template.glob("*.png"))
                        if not imgs:
                            continue
                        tpl = str(imgs[0])
                        for attempt in range(retries):
                            if pyautogui and hasattr(pyautogui, 'locateCenterOnScreen'):
                                try:
                                    loc = pyautogui.locateCenterOnScreen(tpl, confidence=0.8)
                                except Exception:
                                    loc = None
                            else:
                                loc = None
                            if loc:
                                x, y = loc.x, loc.y
                                if driver:
                                    driver.click(x, y)
                                elif pyautogui:
                                    pyautogui.click(x, y)
                                found = True
                                break
                            time.sleep(0.5)
                        break

            if not found:
                raise RuntimeError(f"Template for class '{class_name}' not found on screen")

        else:
            # Unknown step: ignore in dry-run, error in live
            if dry_run:
                log.info(f"[dry] Unknown step {stype}")
            else:
                raise RuntimeError(f"Unknown step type: {stype}")

#
