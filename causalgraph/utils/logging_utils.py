#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

""" Contains functionalities for Logging.
"""

# general imports
import os
import logging
import ecs_logging
# causalgraph imports
from causalgraph.utils.path_utils import get_project_root


def init_logger(logger_name: str,
                file_handler_level= logging.DEBUG,
                console_handler_level= logging.WARNING,
                file_handler= False,
                elastic_style_json= True,
                log_file_dir= None) -> logging.Logger:
    """Initializes a  logger named 'loggerName' with a file handler
    creating 'loggerName.log' and a console handler.

    The logging levels of the handler can be set with kwargs.

    :param logger_name: Name of the logger
    :type logger_name: str
    :param file_handler_leveL: Level for the logfile, defaults to logging.DEBUG
    :type file_handler_leveL: logging Level, optional
    :param console_handler_level: Level for the console output, defaults to logging.ERROR
    :type console_handler_level: logging Level, optional
    :param file_handler: Switch to enable fileHandler, defaults to False
    :type file_handler: bool, optional
    :param elastic_style_json: Switch to enable json logs formatted in elastic style, defaults to True
    :type elastic_style_json: bool, optional
    :param log_file_dir: Path to directory, where log-file should be kept if fileHandler=True,
    defaults to '{project_root}/data/logs/{logger_name}.{log/json}'
    :type log_file_dir: str, optional
    :return: Logger instance
    :rtype: logging.Logger
    """
    # Init main module logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Create human readable format
    format_str = '%(asctime)s %(levelname)-7s %(message)s [%(filename)s:%(lineno)d]'
    human_readable_formatter = logging.Formatter(format_str)
    
    # Create StreamHandler (console handler)
    # Check if StreamHandler exists, adding one if False
    if not any(isinstance(x, logging.StreamHandler) for x in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_handler_level)
        console_handler.setFormatter(human_readable_formatter)
        logger.addHandler(console_handler)
    
    # Create file handler if specified
    if file_handler is True:
        # Set logging file suffix and formatter
        if elastic_style_json is True:
            log_suffix = 'json'
            file_formatter = ecs_logging.StdlibFormatter()
        else:
            log_suffix = 'log'
            file_formatter = human_readable_formatter
        # Compose Path for the file to be stored at
        if log_file_dir is None:
            log_file_path = os.path.join(get_project_root(), 'data', 'logs', f"{logger_name}.{log_suffix}")
        else:
            log_file_path = os.path.join(log_file_dir, 'data', 'logs', f"{logger_name}.{log_suffix}")
            
        # Create FileHandler (file logger)
        # Check if FileHandler exists, adding one if False
        if not any(isinstance(x, logging.FileHandler) for x in logger.handlers):
            filehandler = logging.FileHandler(log_file_path)
            filehandler.setLevel(file_handler_level)
            filehandler.setFormatter(file_formatter)
            logger.addHandler(filehandler)

    return logger
