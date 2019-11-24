from pathlib import Path
from typing import List

from configenerator import Config, ConfigSet, JsonWriter, Template, YamlWriter


def check_other_field(config: Template, configset: List[Template]) -> bool:
    assert (
        config.section.other_field  # type: ignore
    ), f"The other field ({config.section.other_field}) is not True."  # type: ignore
    return True  # None will be considered as True for the purpose of validation


def on_same_version(configset: List[Template]) -> bool:
    versions = {config.version for config in configset}  # type: ignore
    return len(versions) == 1


curdir = Path(__file__).parent


ConfigSet(
    configs=[
        Config(
            templates=[
                Template(
                    version=42,
                    section=Template(field="correct", other_field=True),
                    will_be_modified=1,
                ),
                Template(will_be_modified=lambda x: x * 100),
                Template(version=43, some_other_item="hello"),
            ],
            writer=YamlWriter(curdir / "my-config.yaml"),
            validators=[
                lambda c, cs: c.section.field == "correct",  # type: ignore
                check_other_field,
            ],
        ),
        Config(
            templates=[Template(version=43)],
            writer=JsonWriter(curdir / "other-config.json"),
        ),
    ],
    modifiers=[],
    validators=[],
).materialize()
