"""
Skill loading and registration utilities.
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path
from typing import Dict, Iterable, List, Type

from .base import BaseSkill


def discover_builtin_skills() -> List[Type[BaseSkill]]:
    """Discover Python skills packaged with Envy."""
    skills_package = __name__
    discovered: List[Type[BaseSkill]] = []
    for module_info in pkgutil.iter_modules(__path__, prefix=f"{skills_package}."):  # type: ignore[name-defined]
        if module_info.name.endswith(".base"):
            continue
        module = importlib.import_module(module_info.name)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                discovered.append(attr)
    return discovered


def load_external_skills(path: Path) -> Iterable[Type[BaseSkill]]:
    """
    Load user-provided plugin skills from a folder.
    """
    if not path.exists():
        return []
    skills: List[Type[BaseSkill]] = []
    for py_file in sorted(path.glob("*.py")):
        module_name = py_file.stem
        spec = importlib.util.spec_from_file_location(f"envy.plugins.{module_name}", py_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                    skills.append(attr)
    return skills


def build_skill_registry(external_path: Path | None = None) -> Dict[str, BaseSkill]:
    registry: Dict[str, BaseSkill] = {}
    for skill_cls in discover_builtin_skills():
        registry[skill_cls.name] = skill_cls()
    if external_path:
        for skill_cls in load_external_skills(external_path):
            registry[skill_cls.name] = skill_cls()
    return registry
