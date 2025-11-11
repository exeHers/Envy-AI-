"""Skill packages for Envy assistant."""

from importlib import import_module
from typing import Dict, Type

from .skill_base import Skill, SkillResult


def available_skills() -> Dict[str, Type[Skill]]:
    """Return all registered skills within the skills package."""
    registry: Dict[str, Type[Skill]] = {}
    for module_name in ("code_skill", "research_skill", "sys_control_skill", "reminder_skill"):
        module = import_module(f"skills.{module_name}")
        for attribute in dir(module):
            obj = getattr(module, attribute)
            if isinstance(obj, type) and issubclass(obj, Skill) and obj is not Skill:
                registry[obj.__name__] = obj
    return registry


__all__ = ["Skill", "SkillResult", "available_skills"]
