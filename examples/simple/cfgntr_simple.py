from pathlib import Path

from configenerator import Config, ConfigSet, JsonWriter, Template, YamlWriter


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
        ),
        Config(
            templates=[Template(key="value")],
            writer=JsonWriter(curdir / "other-config.json"),
        ),
    ],
    modifiers=[],
    validators=[],
).materialize()
