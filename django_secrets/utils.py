import inspect
import os
from typing import Iterable


class SettingKeyNotExists(Exception):
    def __init__(self, names: Iterable):
        self.names = names

    def __str__(self):
        return f'SettingKeyNotExists ({", ".join(self.names)})'


def setting(names, default=None, settings_module=None, lookup_env=True, raise_exception=False):
    """
    Helper function to get a Django setting by name. If setting doesn't exists
    it will return a default.
    """
    if settings_module is None:
        stack = inspect.stack()
        frame = stack[3][0]
        settings_module = inspect.getmodule(frame)

    if not isinstance(names, Iterable):
        names = [names]

    for name in names:
        value = getattr(settings_module, name, None)
        if value is not None:
            return value

    if lookup_env:
        for name in names:
            value = os.environ.get(name)
            if value is not None:
                return value

    if raise_exception:
        raise SettingKeyNotExists(names)

    return default
