from inspect import isclass

import django
from django.utils.module_loading import import_string

DJ4 = django.VERSION[0] == 4
DJ5 = django.VERSION[0] == 5


def deserialize_wrapper(caller, **kwargs):
    if isclass(caller):
        return caller
    func = f"{caller.__module__}.{caller.__name__}"
    return import_string(func)
