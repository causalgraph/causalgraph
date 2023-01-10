#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains various helpful methods which are not closely related """

# general imports
from pathlib import Path

# Source: https://stackoverflow.com/questions/25389095/python-get-path-of-root-project-structure/45944002
def get_project_root() -> Path:
    """Returns the project root, relative to the utils.utils_collection.py file"

    :return: Path from root (causalgraph)
    :rtype: Path
    """
    return Path(__file__).parent.parent.parent.absolute()
