import json
import logging
from abc import ABC, abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Union

import yaml

LOGGER = logging.getLogger(__file__)


class Template:
    """Configuration template.

    You can instanciate this with any field you wish. Templates have the ability
    to merge data from  another template.
    """

    def __init__(self: "Template", **kwargs: Any) -> None:
        self.fields = list(kwargs.keys())
        LOGGER.debug(f"New template with keys: {self.fields}")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self: "Template", other: object) -> bool:
        if self.fields != getattr(other, "fields", []):
            return False
        for field in self.fields:
            if getattr(self, field) != getattr(other, field):
                return False
        return True

    def __repr__(self: "Template") -> str:
        return "T" + repr({field: getattr(self, field) for field in self.fields})

    def merge_from(self: "Template", other: "Template") -> None:
        for field in other.fields:
            field_value = getattr(other, field)
            if field not in self.fields:
                self.fields.append(field)
                setattr(self, field, field_value)
            if callable(field_value):
                setattr(self, field, field_value(getattr(self, field)))
            elif isinstance(field_value, Template) and isinstance(
                getattr(self, field), Template,
            ):
                getattr(self, field).merge_from(field_value)
            else:
                setattr(self, field, field_value)
        LOGGER.debug(f"Merge templates, now have keys: {self.fields}")


class NestedTemplate(Template):
    def __init__(
        self: "NestedTemplate", path: Sequence[str], template: Template,
    ) -> None:
        path = list(path)
        field = path.pop(0)
        if path:
            super().__init__(**{field: NestedTemplate(path, template)})
        else:
            super().__init__(**{field: template})


def serialize_to_dict(obj):  # type: ignore
    if isinstance(obj, Template):
        return {field: serialize_to_dict(getattr(obj, field)) for field in sorted(obj.fields)}
    elif isinstance(obj, (list, set, tuple)):
        cls = type(obj)
        return cls([serialize_to_dict(o) for o in obj])
    elif isinstance(obj, dict):
        return {
            serialize_to_dict(key): serialize_to_dict(value)
            for key, value in sorted(obj.items())
        }
    elif isinstance(obj, (str, bytes, int, bool, float)):
        return obj
    elif obj is None:
        return None
    else:
        raise ValueError(f"Can't serialize {type(obj)} object.")


class Writer(ABC):
    @abstractmethod
    def write(self: "Writer", data: Template) -> None:
        pass


ConfigModifierType = Callable[[Template], None]
ConfigValidatorType = Callable[[Template, List[Template]], bool]


class Config:
    __slots__ = ("templates", "writer", "modifiers", "validators", "output")

    def __init__(
        self: "Config",
        templates: List[Template],
        writer: Writer,
        modifiers: Optional[List[ConfigModifierType]] = None,
        validators: Optional[List[ConfigValidatorType]] = None,
    ):
        self.modifiers = modifiers or []
        self.validators = validators or []
        self.writer = writer
        self.templates = templates

    def resolve(self: "Config") -> None:
        # Create an empty template and merge all the templates in.
        self.output = Template()
        for template in self.templates:
            self.output.merge_from(template)
        # Apply the modifiers
        for modifier in self.modifiers:
            modifier(self.output)

    def validate(self: "Config", configset: List[Template]) -> None:
        for validator in self.validators:
            if validator(self.output, configset) not in (True, None):
                raise AssertionError(
                    f"Failed validator {validator.__name__}({self.output}, {configset})",
                )

    def materialize(self: "Config") -> None:
        self.writer.write(self.output)


ConfigSetModifierType = Callable[[List[Template]], None]
ConfigSetValidatorType = Callable[[List[Template]], bool]


class ConfigSet:
    __slots__ = ("configs", "modifiers", "validators", "directory")

    def __init__(
        self: "ConfigSet",
        configs: List[Config],
        modifiers: Optional[List[ConfigSetModifierType]] = None,
        validators: Optional[List[ConfigSetValidatorType]] = None,
    ):
        self.configs = configs
        self.modifiers = modifiers or []
        self.validators = validators or []

    def materialize(self: "ConfigSet") -> None:
        """Generate all configs in this set and write them out.

        This will first resolve all the configurations, then apply the configset
        modifiers. We will then validate each config individually before validating
        the configset. Finally the configs will be written out.
        """
        LOGGER.info("Starting materialization.")
        # Resolve the config, that is merging all the templates and applying modifiers
        for config in self.configs:
            config.resolve()
        config_outputs = [config.output for config in self.configs]
        for modifier in self.modifiers:
            modifier(config_outputs)
        # Validate each config individually
        for config in self.configs:
            config.validate(config_outputs)
        # Validate the ConfigSet itself
        for validator in self.validators:
            if validator(config_outputs) not in (True, None):
                raise AssertionError(
                    f"Failed validator {validator.__name__}({config_outputs})",
                )
        # Finally write everything out.
        for config in self.configs:
            config.materialize()


class YamlWriter(Writer):
    __slots__ = ("target",)

    def __init__(self: "YamlWriter", target: Union[str, Path]) -> None:
        self.target = Path(target)

    def write(self: "YamlWriter", data: Template) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        with open(self.target, "w") as fd:
            yaml.dump(serialize_to_dict(data), fd)


class JsonWriter(Writer):
    __slots__ = ("target",)

    def __init__(self: "JsonWriter", target: Union[str, Path]) -> None:
        self.target = Path(target)

    def write(self: "JsonWriter", data: Template) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        with open(self.target, "w") as fd:
            json.dump(serialize_to_dict(data), fd, sort_keys=True, indent=4)
            fd.write("\n")


class IniWriter(Writer):
    __slots__ = ("target",)

    def __init__(self: "IniWriter", target: Union[str, Path]) -> None:
        self.target = Path(target)

    def write(self: "IniWriter", data: Template) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        config = ConfigParser()
        for section, kv_pairs in serialize_to_dict(data).items():
            config[section] = kv_pairs
        with open(self.target, "w") as fd:
            config.write(fd)
