# January 2022, Lewis Gaul

__all__ = ("run_main_entrypoint",)

import importlib.util
import types


def run_main_entrypoint() -> types.ModuleType:
    """
    Run minegauler via the __main__ module.

    :return:
        The __main__ module namespace.
    """
    module = types.ModuleType("minegauler.__main__")
    spec = importlib.util.find_spec("minegauler.__main__")
    spec.loader.exec_module(module)
    return module
