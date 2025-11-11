# Custom Skills

Drop Python modules in this directory to extend Envy. Each module should define a subclass of `envy.skills.base.BaseSkill`:

```python
from envy.skills.base import BaseSkill, SkillContext, SkillResult


class HelloSkill(BaseSkill):
    name = "hello"
    description = "Says hello."

    def matches(self, transcript: str) -> bool:
        return "say hello" in transcript.lower()

    async def execute(self, context: SkillContext) -> SkillResult:
        return SkillResult(success=True, message="Hello from Envy!")
```

Restart Envy to load the new skill automatically.
