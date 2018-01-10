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

import toastbot.botfunctions.diceroller as diceroller
import toastbot.botfunctions.logbot as logbot


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

    engine = logbot.initialize_engine()
    session = logbot.create_session(engine)

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

    help_startlog = (
        "- Start logging: !startlog <log name>-<Name 1>-<Name 2>-...-<Name N>\n"
        "Start logging by naming the log, and adding the displayed names of players.\n"
        "The log name will be used to end the log at the end of the event."
    )

    @bot.command(pass_context=True, help=help_startlog)
    @asyncio.coroutine
    def startlog(context):
        logging.info('Initializing log...')
        command = context.message.content
        split_command = command.split(' ')
        try:
            command_contents = split_command[1]
            command_params = command_contents.split('-')
            command_log_name = command_params[0]
            command_characters = command_params[1:]
        except IndexError:
            error_msg = 'Error: Not all parameters specified for log start. Use !help startlog for more info.'
            yield from bot.say(content=error_msg)
        else:
            log_initialized_timestamp = context.message.timestamp

            initialized_info_string = 'Started log {} at {}\nCharacters: {}.'.format(
                command_log_name, log_initialized_timestamp, '; '.join(command_characters))
            logging.info(initialized_info_string)
            created_session = logbot.create_session(engine)
            logbot.add_log(created_session, command_log_name, log_initialized_timestamp)
            log_id = logbot.get_log_id(created_session, command_log_name, log_initialized_timestamp)
            for name in command_params[1:]:
                logging.info('Found names in command: {}'.format('; '.join(command_characters)))
                try:
                    logbot.LogSessionConfigs.add_log_to_user(name, log_id)
                except KeyError:
                    logbot.LogSessionConfigs.add_user(name)
                    logbot.LogSessionConfigs.add_log_to_user(name, log_id)
            yield from bot.say(content=initialized_info_string)


    @bot.listen('on_message')
    @asyncio.coroutine
    def listen_for_text(message):
        try:
            author_name = message.author.nick if message.author.nick is not None else message.author.name
        except AttributeError:
            author_name = message.author.name
        logging.info('Heard message from {}.'.format(author_name))
        if author_name in logbot.LogSessionConfigs.active_logs:
            logging.info('User in active log.')
            created_session = logbot.create_session(engine)
            for log_id in logbot.LogSessionConfigs.active_logs[author_name]:
                created_session = logbot.add_new_text(
                    session=created_session,
                    timestamp=message.timestamp,
                    character_name=author_name,
                    username=message.author.name,
                    text=message.content,
                    log_id=log_id
                )

    help_endlog = (
        "- End logging: !endlog <log name>-<Name 1>-<Name 2>-...-<Name N>\n"
        "End the log with this command."
    )

    @bot.command(pass_context=True, help=help_endlog)
    @asyncio.coroutine
    def endlog(context):
        try:
            log_name = context.message.content.split(' ')[1]
            created_session = logbot.create_session(engine)
        except IndexError:
            yield from bot.say('Please specify name of log to end.')
        else:
            log_id = logbot.get_log_id(created_session, log_name)
            for character in list(logbot.LogSessionConfigs.active_logs):
                if len(logbot.LogSessionConfigs.active_logs[character]) == 1:
                    del logbot.LogSessionConfigs.active_logs[character]
                else:
                    logbot.LogSessionConfigs.active_logs[character].remove(log_id)
            ended_info_string = 'Ended log {name}.'.format(name=log_name)
            logging.info(ended_info_string)
            yield from bot.say(ended_info_string)

    @bot.command(pass_context=True)
    @asyncio.coroutine
    def getlog(context):
        requestor = context.message.author
        try:
            log_name = context.message.content.split(' ')[1]
        except IndexError:
            yield from bot.say('Please specify log to receive.')
        else:
            created_session = logbot.create_session(engine)
            log_id = logbot.get_log_id(created_session, log_name)
            responses = logbot.get_text(created_session, log_id)
            full_text = [str(response) for response in responses]
            full_text = '\n'.join(full_text)
            yield from bot.send_message(requestor, full_text)

    logging.info('Retrieving API details...')
    config = botconf.read_api_configuration(DEFAULT_API_CREDENTIALS_LOCATION)
    token = config[DEFAULT_BOT_TOKEN_SECTION][DEFAULT_BOT_TOKEN_VALUE_NAME]
    logging.info('Running bot...')
    bot.run(token)
    logging.info('Script finished.')

if __name__ == "__main__":
    main()
