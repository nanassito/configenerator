from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from textwrap import dedent
from unittest.mock import Mock, call

import pytest

from configenerator import (
    Config,
    ConfigSet,
    IniWriter,
    JsonWriter,
    Template,
    YamlWriter,
)


def test_validates_config():
    validator = Mock(return_value=True)
    configset_outputs = [Mock(), Mock()]
    config = Config(
        templates=[Template(a=1, b=2), Template(b=3, c=4)],
        validators=[validator],
        writer=Mock(),
    )
    config.output = Mock()

    config.validate(configset_outputs)

    assert validator.call_args == call(config.output, configset_outputs)


def test_invalid_config():
    validator = Mock(return_value=False, __name__="mock")
    config = Config(
        templates=[Template(a=1, b=2), Template(b=3, c=4)],
        validators=[validator],
        writer=Mock(),
    )
    config.output = Mock()
    with pytest.raises(AssertionError):
        config.validate([])


def test_modifies_config():
    modifier = Mock()
    config = Config(
        templates=[Template(a=1, b=2), Template(b=3, c=4)],
        modifiers=[modifier],
        writer=Mock(),
    )
    config.resolve()

    expected = Template(a=1, b=3, c=4)
    assert config.output == expected
    assert modifier.call_args == call(expected)


def test_validates_configset():
    validator = Mock(return_value=True)
    configset = ConfigSet(configs=[Mock(), Mock()], validators=[validator])
    configset.materialize()

    assert validator.call_args == call([c.output for c in configset.configs])


def test_invalid_configset():
    validator = Mock(__name__="mock", return_value=False)
    configset = ConfigSet(configs=[Mock(), Mock()], validators=[validator])
    with pytest.raises(AssertionError):
        configset.materialize()


def test_modifies_configset():
    modifier = Mock()
    configset = ConfigSet(configs=[Mock(), Mock()], modifiers=[modifier])
    configset.materialize()

    assert modifier.call_args == call([c.output for c in configset.configs])


def create_and_attach_mock(mock_manager, name):
    mock = Mock()
    mock_manager.attach_mock(mock, name)
    return mock


def test_materialize():
    mock_manager = Mock()
    config = Mock(output=Template(a=1, b=2))
    mock_manager.attach_mock(config, "config")
    configset_modifier = create_and_attach_mock(mock_manager, "configset_modifier")
    configset_validator = create_and_attach_mock(mock_manager, "configset_validator")
    configset_validator.return_value = True
    configset = ConfigSet(
        configs=[config],
        modifiers=[configset_modifier],
        validators=[configset_validator],
    )

    configset.materialize()

    assert mock_manager.mock_calls == [
        call.config.resolve(),
        call.configset_modifier([config.output]),
        call.config.validate([config.output]),
        call.configset_validator([config.output]),
        call.config.materialize(),
    ]


def test_yaml_writer():
    data = Template(key="value", items=[Template(a=1), Template(a=2), Template(a=3)])
    with NamedTemporaryFile("r") as fd:
        YamlWriter(fd.name).write(data)
        result = fd.read().strip()
    expected = dedent(
        """
        items:
        - a: 1
        - a: 2
        - a: 3
        key: value
        """
    ).strip()
    assert expected == result


def test_json_writer():
    data = Template(key="value", items=[Template(a=1), Template(a=2), Template(a=3)])
    with NamedTemporaryFile("r") as fd:
        JsonWriter(fd.name).write(data)
        result = fd.read().strip()
    expected = dedent(
        """
        {
            "items": [
                {
                    "a": 1
                },
                {
                    "a": 2
                },
                {
                    "a": 3
                }
            ],
            "key": "value"
        }
        """
    ).strip()
    assert expected == result


def test_ini_writer():
    data = Template(section1=Template(prop_a=1), section2=Template(prop_a=2, prop_b=3))
    with NamedTemporaryFile("r") as fd:
        IniWriter(fd.name).write(data)
        result = fd.read().strip()
    expected = dedent(
        """
        [section1]
        prop_a = 1

        [section2]
        prop_a = 2
        prop_b = 3
        """
    ).strip()
    assert result == expected


@pytest.mark.parametrize(
    ("writer_cls", "data"), [(IniWriter, {}), (JsonWriter, {}), (YamlWriter, {})],
)
def test_writer_creates_dir(writer_cls, data):
    with TemporaryDirectory() as directory:
        target = Path(directory, writer_cls.__name__, "test.out")
        writer_cls(target).write(data)
        assert target.exists()
