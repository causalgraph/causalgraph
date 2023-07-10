#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains various helpful methods which are not closely related """

# general imports
from pathlib import Path
from typing import Union, get_origin, get_args
from functools import wraps
from inspect import signature, Parameter


# Source: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure/45944002
def get_project_root() -> Path:
    """Returns the project root, relative to the utils.utils_collection.py file"

    :return: Path from root (causalgraph)
    :rtype: Path
    """
    return Path(__file__).parent.parent.parent.absolute()


def strict_types(f):
    """A function decorator that enforces strict typing for the decorated function's arguments.
    This wrapper verifies the types of the arguments passed to the decorated function against their type hints.
    If a type hint is specified for an argument and the argument's value does not match the expected type,
    a TypeError is raised.

    :usage:
        @strict_types
        def my_function(arg1: int, arg2: str) -> bool:
            # Function implementation
    :note:
        - This wrapper supports type hints including Union[] and float conversions from int.

    :param f: The function to be decorated.
    :type f: function
    :returns: The decorated function with type checking enforced.
    :rtype: function
    """
    @wraps(f)
    def type_checker(*args, **kwargs):

        hints = signature(f).parameters

        all_args = kwargs.copy()
        all_args.update(dict(zip(f.__code__.co_varnames, args)))

        for key, arg_value in all_args.items():
            if key in hints:
                param_type = hints[key].annotation

                if param_type == Parameter.empty:
                    continue

                if get_origin(param_type) is Union:
                    # Allow the specified types in the Union or None
                    if arg_value is not None and not isinstance(arg_value, get_args(param_type)):
                        raise TypeError(f"Type of {key} is {type(arg_value)} but should be {param_type}")
                elif param_type is float and isinstance(arg_value, int):
                    # Convert integer to float if a float parameter is expected
                    arg_value = float(arg_value)
                elif not isinstance(arg_value, param_type):
                    raise TypeError(f"Type of {key} is {type(arg_value)} but should be {param_type}")

                all_args[key] = arg_value

        return f(*args, **kwargs)

    return type_checker