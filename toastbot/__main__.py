import collections
import logging
import asyncio
import importlib
import pip

import toastbot.toast as toast


try:
    import discord
    import discord.ext.commands as commands
except ImportError:
    print('Installing discord package...')
    pip.main(['install', 'discord'])
    import discord
    import discord.ext.commands as commands
finally:
    print('Importing discord package...')
    globals()['discord'] = importlib.import_module('discord')
    globals()['commands'] = importlib.import_module('discord.ext.commands')

import toastbot.configuration as botconf
import toastbot.defaultlogger as logger
from toastbot import botfunctions as diceroller


DEFAULT_API_CREDENTIALS_LOCATION = "configuration/api_keys.txt"
DEFAULT_CONFIG_LOCATION = "configuration/config.txt"

DEFAULT_BOT_TOKEN_SECTION = 'discord'
DEFAULT_BOT_TOKEN_VALUE_NAME = 'BotToken'

DEFAULT_LOGGING_SECTION = 'logging'
DEFAULT_LOG_LEVEL_VALUE_NAME = 'LogLevel'


def _monospace_message(str):
    msg = "`{str}`".format(str=str)
    return msg


def _create_roll_response(roll_results, author_name):
    if len(roll_results.raw_rolls) > 10:
        msg_template = _create_long_roll_response(roll_results, author_name)
    else:
        msg_template = _create_simple_roll_response(roll_results, author_name)
    return msg_template


def _create_simple_roll_response(roll_results, author_name):
    msg_template = "\nAuthor: {author}\n" \
                   "{roll_results}".format(author=author_name, roll_results=str(roll_results))
    return msg_template


def _create_long_roll_response(roll_results, author_name):
    value_counter = collections.Counter(roll_results.raw_rolls)
    mod_value_counter = collections.Counter(roll_results.modified_rolls)
    raw_vals = list(value_counter.keys())
    raw_vals.sort()
    mod_vals = list(mod_value_counter.keys())
    mod_vals.sort()
    count = [value_counter[value] for value in raw_vals]

    values = [len(str(x)) for x in raw_vals + mod_vals + count]
    pad_len = max(values)

    results_table = [
        '{mod_val} ({raw_val}): {count}'.format(
            mod_val=str(mod).ljust(pad_len, ' '),
            raw_val=str(raw).ljust(pad_len, ' '),
            count=str(count).ljust(pad_len, ' ')
        )
        for mod, raw, count
        in zip(mod_vals, raw_vals, count)
        ]

    formatted_colnames = "Value (Unmodified): Count"
    msg_base = [
        "\nAuthor: {author}".format(author=author_name),
        formatted_colnames
    ]
    result_msg = '\n'.join(msg_base + results_table)
    return result_msg


def init_logging():
    config = botconf.read_api_configuration(DEFAULT_CONFIG_LOCATION)
    logging_level_setting = config[DEFAULT_LOGGING_SECTION][DEFAULT_LOG_LEVEL_VALUE_NAME]
    logging_level = logger.LOG_LEVEL_MAP[logging_level_setting]
    logger.init_logging(level=logging_level)
    logging.info('Logging initialized, level: {}'.format(logging_level_setting))


def main():
    init_logging()

    bot_prefix = "!"
    logging.debug('Bot prefix set to: {}'.format(bot_prefix))
    logging.info('Initializing Discord Bot...')
    bot = toast.ToastBot(command_prefix=bot_prefix, pm_help=True)
    logging.info('Initializing Dicebot...')
    dice = diceroller.Dicebot()

    @bot.event
    @asyncio.coroutine
    def on_ready():
        logging.info("Bot online!")

    @bot.command(pass_context=True)
    @asyncio.coroutine
    def test(context):
        author = context.message.author
        logging.info('Bot received test command from {}'.format(author))

        msg_text = "\nAuthor: {author}\nBot is online.".format(author=author.display_name)
        msg_text = _monospace_message(msg_text)
        logging.info('Bot responded to test command.')
        yield from bot.say(content=msg_text)

    help_roll = ("- Roll dice: !roll <i>d<j>[+-][k] - type !help roll for more details.\n"
                 "i = # of dice\n"
                 "j = # of sides per die\n"
                 "k = # to add or subtract from each die\n"
                 "Elements in square brackets are optional.\n"
                 "Ex. !roll 2d10+5, or !roll 1d20"
                 )

    @bot.command(pass_context=True, help=help_roll)
    @asyncio.coroutine
    def roll(context):
        author = context.message.author
        logging.info('Bot received roll command from {}.'.format(author))
        try:
            results = dice.roll(context.message.content)
            msg_text = _create_roll_response(results, author.display_name)
        except diceroller.DiceRollFormatError:
            msg_text = "Valid dice roll command not found. Command: {}\nType !help roll for dice-rolling help.".format(
                context.message.content
            )
        msg_text = _monospace_message(msg_text)
        logging.info('Bot responded to roll command.')
        yield from bot.say(content=msg_text)

    logging.info('Retrieving API details...')
    config = botconf.read_api_configuration(DEFAULT_API_CREDENTIALS_LOCATION)
    token = config[DEFAULT_BOT_TOKEN_SECTION][DEFAULT_BOT_TOKEN_VALUE_NAME]
    logging.info('Running bot...')
    bot.run(token)
    logging.info('Script finished.')

if __name__ == "__main__":
    main()
