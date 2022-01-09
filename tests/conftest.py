# January 2022, Lewis Gaul


def pytest_addoption(parser):
    parser.addoption("--benchmark", action="store_true", help="run benchmark tests")


def pytest_configure(config):
    if not config.option.benchmark:
        if getattr(config.option, "markexpr", None):
            prefix = config.option.markexpr + " and "
        else:
            prefix = ""
        setattr(config.option, "markexpr", prefix + "not benchmark")
