"""
Utility to read in bot configuration and setup.

Config file has format:

#####
[discord]
bot_token = <Bot token>

#####
"""

import configparser
import sys
import os
import logging


def _get_path_to_config(config_location):
    logging.info('Retrieving configuration...')
    main_path = os.path.abspath(sys.modules['__main__'].__file__)
    root_path = os.path.dirname(main_path)
    config_path = os.path.join(root_path, config_location)
    logging.info('Full path found.')
    return config_path


def read_api_configuration(config_location):
    logging.info('Reading API configuration from file...')
    config_location = _get_path_to_config(config_location)
    config = configparser.ConfigParser()
    config.read(config_location)
    logging.info('Configuration successfully read.')
    return config
