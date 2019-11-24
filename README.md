# Configenerator

Configenerator is a library to make it easier to manage large configurations. It helps in several ways:
* Pre-commit hook to materialize the configuration.
* Ability to layer templates.
* Strong validation primitives.

The goal of Configenerator is to help with managing pool of configurations. Think of a cluster configuration or application configuration for something that has a lot of different deployment, all similar to one another with just a few changes.


# Why not Jinja or Jsonnet
While Configenerator overlaps with Jinja and Jsonnet for the ability to templetize configuration, it is different in that it by default materialize the files at pre-commit, not hidden into some build system. Becuase `ConfigSet` are python objects, it is easy to have inheritance, modify then, and otherwise manipulate them to achieve the desired result. This also means that we can add strong validation functions to a `Config` and `ConfigSet`.

# How does Configenerator works ?

A Configenerator configuration is a `ConfigSet`. A `ConfigSet` contains a list of `Config` and has a list of modifiers and validators that will be applied on all the `Config.output` in the `ConfigSet`. A `ConfigSet` generally represent a directory where all the configuration will be written out.

A `Config` is an object has a list of `Template`, a list of modifiers and validators to be applied on the result of the templates. It also has a `Writer` which will be responsible for writing the resulting configuration out.

A `Template` is an object with arbitrary fields. You can merge Templates together. Indeed when `resolve()`ing a `Config`, a new empty `Template()` is created and all the `Config`'s templates are merged into it. Contrary to python dictionary, Template merge in depth, that means that `T(a=T(b=1)).merge_from(T(a=T(c=2)))` will result in `T(a=T(b=1, c=2))`. If the value of a Template field is a `Callable`, then it is called with the previous value as parameter and the result is assigned to the field.

# Examples
You can check the `examples` directory.

# Validators
There are two types of validators, one for `Config` and one for `ConfigSet` with the following signature:
* `config_validator(config: Template, configset: List[Template]) -> bool`
* `configset_validator(configset: List[Template]) -> bool`

Note that is your validator does not return anything (`None`), we will assume that the configuration is valid.
It is advised against abusing validators to modify fields. This might be blocked in a future iteration. You should use modifiers instead.

# Pre-commit:
The files that materialize a `ConfigSet` should match the regex `cfgr_\w+.py`.

You can then add the following pre-commit hook in your `.pre-commit-config.yaml`:
```
repos:
- repo: https://github.com/nanassito/configenerator
  rev: 1.0.0
  hooks:
  - id: materialize
```
