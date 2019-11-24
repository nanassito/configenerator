r"""Find all the the cfgr_\w+.py files in the repository and materializes them."""

import os
import sys
from contextlib import contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Iterator


@contextmanager
def syspath(root: str) -> Iterator[None]:
    added = False
    if root not in sys.path:
        sys.path.append(root)
        added = True
    yield
    if added:
        sys.path.remove(root)


def materialize(directory: str, file: str) -> None:
    root = Path(directory)
    module_path = os.path.join(directory, file)
    module_name = file.rsplit(".", 1)[0]
    while (root / "__init__.py").exists():
        module_name = f"{root.parts[-1]}.{module_name}"
        root = root.parent
    with syspath(str(root)):
        print(f"Importing {module_name} from {module_path}")
        module_spec = spec_from_file_location(module_name, module_path)
        module_obj = module_from_spec(module_spec)
        print(f"Executing {module_name}")
        module_spec.loader.exec_module(module_obj)  # type: ignore


def main() -> None:
    for dirpath, _dirnames, filenames in os.walk(os.getcwd()):
        for filename in filenames:
            if filename.startswith("cfgntr_") and filename.endswith(".py"):
                materialize(dirpath, filename)


if __name__ == "__main__":
    main()
