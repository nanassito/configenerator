from setuptools import setup


setup(
    name="configenerator",
    version="1.0.0",
    description="Small library to treat configuration as code (inheritance, templates, modifiers, tests, etc.)",
    url="https://github.com/nanassito/configenerator",
    maintainer="Dorian Jaminais-Grellier",
    maintainer_email="configenerator@jaminais.fr",
    py_modules=["configenerator"],
    install_requires=["pyyaml"],
    extras_require={':python_version=="3.6"': ["dataclasses"]},
)
