import pytest

from configenerator import NestedTemplate, Template, serialize_to_dict


@pytest.mark.parametrize(
    ("left", "right", "result"),
    [
        (Template(), Template(), True),
        (Template(a=1), Template(a=1), True),
        (Template(a=1), Template(a=2), False),
        (Template(a=Template(a=1)), Template(a=Template(a=1)), True),
        (Template(a=Template(a=1)), Template(a=Template(a=2)), False),
        (Template(a=1, b=2), Template(b=2), False),
        (Template(a=1), Template(a=1, b=2), False),
    ],
)
def test_template_comparizon(left, right, result):
    assert (left == right) is result


@pytest.mark.parametrize(
    ("original", "overlay", "result", "msg"),
    [
        (Template(), Template(a=1), Template(a=1), "Merging to an empty template."),
        (Template(a=1), Template(), Template(a=1), "Merging from an empty template."),
        (Template(a=1), Template(b=2), Template(a=1, b=2), "Adding a new field."),
        (Template(a=1), Template(a=2), Template(a=2), "Overriding a field."),
        (
            Template(a=2),
            Template(a=lambda x: x * 10),
            Template(a=20),
            "Applying a function.",
        ),
        (
            Template(a=Template(b=1)),
            Template(a=Template(c=2)),
            Template(a=Template(b=1, c=2)),
            "Nesting Templates.",
        ),
    ],
)
def test_merge(original, overlay, result, msg):
    original.merge_from(overlay)
    assert original == result, msg


@pytest.mark.parametrize(
    ("nested", "result", "msg"),
    [
        (NestedTemplate(("a"), "value"), Template(a="value"), "First level"),
        (
            NestedTemplate(("a", "b", "c"), "value"),
            Template(a=Template(b=Template(c="value"))),
            "Arbitrary level",
        ),
    ],
)
def test_nested_templates(nested, result, msg):
    assert nested == result, msg


@pytest.mark.parametrize(
    ("template", "result", "msg"),
    [
        (Template(), {}, "Empty template"),
        (Template(a=1, b="value"), {"a": 1, "b": "value"}, "Simple template"),
        (
            Template(a=1, b=Template(c="value")),
            {"a": 1, "b": {"c": "value"}},
            "Nested template",
        ),
        (None, None, "None"),
        (True, True, "bool"),
        (42, 42, "int"),
        (42.0, 42.0, "float"),
        ("value", "value", "str"),
        (b"value", b"value", "bytes"),
        ([1, "b"], [1, "b"], "list of simple types"),
        ({1, "b"}, {1, "b"}, "set of simple types"),
        ((1, "b"), (1, "b"), "tuple of simple types"),
        ({"a": 2}, {"a": 2}, "dict of simple types"),
        ([1, {"b": 2}], [1, {"b": 2}], "nested collections"),
        ([1, {"b": Template(c=3)}], [1, {"b": {"c": 3}}], "nested collections"),
    ],
)
def test_serialization(template, result, msg):
    assert serialize_to_dict(template) == result, msg


def test_serialization_fails():
    with pytest.raises(ValueError):
        serialize_to_dict(object())
