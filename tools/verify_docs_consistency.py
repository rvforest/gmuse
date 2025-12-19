import importlib
import inspect
import os
import pkgutil
import sys
from pathlib import Path


def get_public_modules(package_name):
    package = importlib.import_module(package_name)
    path = package.__path__
    prefix = package.__name__ + "."

    modules = []
    for _, name, ispkg in pkgutil.walk_packages(path, prefix):
        if not name.split(".")[-1].startswith("_"):
            modules.append(name)
    return modules


def verify_docs_consistency(src_dir, docs_dir):
    sys.path.insert(0, src_dir)

    try:
        public_modules = get_public_modules("gmuse")
    except ImportError as e:
        print(f"Error importing gmuse: {e}")
        sys.exit(1)

    print(f"Found {len(public_modules)} public modules.")

    errors = []
    for module_name in public_modules:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            print(f"Could not import {module_name}")
            continue

        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue

            if inspect.isfunction(obj) or inspect.isclass(obj):
                if hasattr(obj, "__module__") and obj.__module__ != module_name:
                    continue  # Imported symbol

                if not obj.__doc__:
                    errors.append(f"{module_name}.{name}: Missing docstring")

    if errors:
        print("Consistency errors found:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    else:
        print("Docs consistency check passed.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_docs_consistency.py <src_dir> <docs_dir>")
        sys.exit(1)
    verify_docs_consistency(sys.argv[1], sys.argv[2])
