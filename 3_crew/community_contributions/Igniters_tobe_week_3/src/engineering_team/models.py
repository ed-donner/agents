from pydantic import BaseModel, model_validator


class ModuleSpec(BaseModel):
    name: str
    classes: list[str]
    functions: list[str]
    depends_on: list[str]
    description: str


class SystemArchitecture(BaseModel):
    modules: list[ModuleSpec]
    build_order: list[str]

    @model_validator(mode="after")
    def validate_architecture(self):
        names = [module.name for module in self.modules]
        if len(names) != len(set(names)):
            raise ValueError("Module names must be unique")
        if "app.py" in names:
            raise ValueError("app.py must be created by the integration task")
        if len(self.build_order) != len(names) or set(self.build_order) != set(names):
            raise ValueError("build_order must include each module exactly once")
        positions = {name: index for index, name in enumerate(self.build_order)}
        for module in self.modules:
            seen = set()
            for dependency in module.depends_on:
                if dependency == module.name:
                    raise ValueError(f"{module.name} cannot depend on itself")
                if dependency in seen:
                    raise ValueError(f"{module.name} has duplicate dependency {dependency}")
                if dependency not in positions:
                    raise ValueError(f"{module.name} depends on unknown module {dependency}")
                if positions[dependency] >= positions[module.name]:
                    raise ValueError(f"build_order must place {dependency} before {module.name}")
                seen.add(dependency)
        if not any(not module.depends_on for module in self.modules):
            raise ValueError("At least one module must have no dependencies")
        return self
