"""Plugin Manager — lifecycle hook execution (Phase 11).

Lifecycle hooks (called in registration order):
  before_plan(prompt, project) -> None
  after_validation(plan, result) -> None
  before_execution(plan) -> None
  after_execution(plan, result) -> None

Plugins are auto-loaded from the plugins/ directory.
Each plugin module must expose a register(manager) function.
"""

import importlib
import logging
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

HookFn = Callable[..., None]


class PluginManager:
    def __init__(self) -> None:
        self._hooks: dict[str, list[HookFn]] = {
            "before_plan":       [],
            "after_validation":  [],
            "before_execution":  [],
            "after_execution":   [],
        }

    def register(self, hook: str, fn: HookFn) -> None:
        if hook not in self._hooks:
            raise ValueError(f"Unknown hook: '{hook}'. Valid: {list(self._hooks)}")
        self._hooks[hook].append(fn)

    def fire(self, hook: str, **kwargs: Any) -> None:
        for fn in self._hooks.get(hook, []):
            try:
                fn(**kwargs)
            except Exception:
                log.exception(f"Plugin hook '{hook}' raised an exception in {fn}")

    def load_plugins_from_dir(self, plugins_dir: Path) -> int:
        """Auto-discover and load all plugin modules in plugins_dir."""
        loaded = 0
        if not plugins_dir.exists():
            return 0
        for py_file in sorted(plugins_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"plugins.{py_file.stem}"
            try:
                mod = importlib.import_module(module_name)
                if hasattr(mod, "register"):
                    mod.register(self)
                    loaded += 1
                    log.info(f"Loaded plugin: {py_file.name}")
            except Exception:
                log.exception(f"Failed to load plugin: {py_file.name}")
        return loaded


# Global singleton
plugin_manager = PluginManager()
