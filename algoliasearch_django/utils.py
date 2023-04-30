import inspect

from django.utils import six


def func_accepts_kwargs(func):
    """
    Shameless copy-paste from django.utils.inspect.

    FIXME: when dropping support for Django 1.7, remove this code
    """
    if six.PY2:
        # Not all callables are inspectable with getargspec, so we'll
        # try a couple different ways but in the end fall back on assuming
        # it is -- we don't want to prevent registration of valid but weird
        # callables.
        try:
            argspec = inspect.getargspec(func)
        except TypeError:
            try:
                argspec = inspect.getargspec(func.__call__)
            except (TypeError, AttributeError):
                argspec = None
        return not argspec or argspec[2] is not None

    return any(
        p for p in inspect.signature(func).parameters.values()
        if p.kind == p.VAR_KEYWORD
    )


def func_supports_parameter(func, parameter):
    """
    Shameless copy-paste from django.utils.inspect.

    FIXME: when dropping support for Django 1.7, remove this code
    """
    if six.PY3:
        return parameter in inspect.signature(func).parameters
    else:
        args, varargs, varkw, defaults = inspect.getargspec(func)
        return parameter in args
