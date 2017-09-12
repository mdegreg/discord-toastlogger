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


def _get_path_to_config(config_location):
    main_path = os.path.abspath(sys.modules['__main__'].__file__)
    root_path = os.path.dirname(main_path)
    config_path = os.path.join(root_path, config_location)
    return config_path


def read_configuration(config_location):
    config_location = _get_path_to_config(config_location)
    print(config_location)
    config = configparser.ConfigParser()
    config.read(config_location)
    print(config.__dict__)
    print(config.sections())
    print(config['discord'])
    return config
