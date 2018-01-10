"""
Dicebot functionality
"""
import random
import re
import logging

ADD = "+"
SUBTRACT = "-"
DEFAULT_MAX_DICE = 100
DEFAULT_MAX_SIDES = 1000
DEFAULT_MAX_MODIFIER = 1000


class DiceRollError(ValueError):
    """
    This error should be used if there is a general error in execution of the dice roll.
    """
    pass


class DiceRollFormatError(DiceRollError):
    """
    This error is used if there is a misformatted or otherwise unparseable error.
    """
    pass


class CommandParserConfig:
    def __init__(
            self,
            permitted_operations="{}{}".format(ADD, SUBTRACT),
            max_num_dice=DEFAULT_MAX_DICE,
            max_num_sides=DEFAULT_MAX_SIDES,
            max_modifier=DEFAULT_MAX_MODIFIER
    ):
        self.permitted_operations = permitted_operations
        self.max_num_dice = max_num_dice
        self.max_num_sides = max_num_sides
        self.max_modifier = max_modifier


class CommandParser:

    def __init__(self, command_parser_config=CommandParserConfig()):
        self.config = command_parser_config
        self._command_parsing_regex = (
            "[^0-9]*([0-9]+)d([0-9]+)(?:([" +
            "{mods}".format(mods=self.config.permitted_operations) +
            "]{0,1})([0-9]+)){0,1}"
        )
        logging.info('Command parser initialized.')
        logging.debug('Allowed operations: {}'.format(self.config.permitted_operations))
        logging.debug('Maximum dice: {}'.format(self.config.max_num_dice))
        logging.debug('Maximum sides: {}'.format(self.config.max_num_sides))
        logging.debug('Maximum modifier: {}'.format(self.config.max_modifier))
        logging.debug('Command regex: {}'.format(self._command_parsing_regex))

    def parse_command(self, raw_command):
        logging.info('Command received: {}'.format(raw_command))
        result = re.match(self._command_parsing_regex, raw_command)
        if result is None:
            logging.error('Unparseable command: {}'.format(raw_command))
            raise DiceRollFormatError("Regex failed to match command. Command: {}".format(raw_command))
        else:
            #  Group 0 is the entire match.
            num_dice = int(result.group(1))
            logging.debug('# of dice: {}'.format(num_dice))
            num_sides = int(result.group(2))
            logging.debug('# of sides: {}'.format(num_sides))
            operation_sign = result.group(3) if result.group(3) else None
            logging.debug('Operation: {}'.format(operation_sign))
            modifier = int(result.group(4)) if result.group(4) else None
            logging.debug('Modifier: {}'.format(modifier))
            command = Command(num_dice, num_sides, modifier, operation_sign, raw_command)
            self._validate_command(command)
            logging.info('Command parsed.')
            return command

    def _validate_command(self, command):
        if command.modifier is not None and command.modifier > self.config.max_modifier:
            exception_msg = "Error: Specified roll modifier is too large. Requested: {}, maximum is {}.".format(
                command.modifier, self.config.max_modifier
            )
            raise DiceRollError(exception_msg)
        elif command.roll_operation is not None and command.roll_operation not in self.config.permitted_operations:
            #  Provide standard initial output string for error.
            exception_msg = "Error: Specified modifier operation is unsupported.\nSupported operations: {}".format(
                self.config.permitted_operations
            )
            raise DiceRollError(exception_msg)

        elif command.num_dice > self.config.max_num_dice:
            exception_msg = "Error: Specified number of dice is too large. Requested: {}, maximum is {}.".format(
                command.num_dice, self.config.max_num_dice
            )
            raise DiceRollError(exception_msg)
        elif command.num_sides > self.config.max_num_sides:
            exception_msg = "Error: Specified size of dice is too large. Requested: {}, maximum is {}.".format(
                command.num_sides, self.config.max_num_sides
            )
            raise DiceRollError(exception_msg)
        else:
            logging.info('Command passed validation checks.')
            pass


class Dicebot:
    """
    Bot to provide dice rolls on request.
    """
    MIN_NUM_SIDES_ON_DICE = 1

    def __init__(self, command_parser=CommandParser()):
        logging.info('Dicebot initialized.')
        self.command_parser = command_parser

    def set_seed(self, value):
        random.seed(value)
        logging.info('Dicebot seed set to {}'.format(value))
        return "Dicebot seed set to {}".format(value)

    def roll(self, raw_command):
        logging.info('Dicebot received command: {}'.format(raw_command))
        command = self.command_parser.parse_command(raw_command)
        raw_results = self._roll_dice(command)
        modified_results = self._apply_modifier(raw_results, command)
        results = DiceResults(raw_results, modified_results, command)
        logging.info('Dicebot returning results for command.')
        return results

    @staticmethod
    def _roll_dice(command):
        logging.debug('Rolling dice for command: {}'.format(str(command)))
        #  List comprehension to generate random numbers for each desired die.
        raw_results = [random.randint(Dicebot.MIN_NUM_SIDES_ON_DICE, command.num_sides)
                       for i in range(command.num_dice)]
        logging.debug('Dicebot returning results: {}.'.format(raw_results))
        return raw_results

    def _apply_modifier(self, raw_results, command):
        logging.debug('Dicebot applying modifier: {} to results: {}'.format(command.modifier, raw_results))
        if command.modifier is not None:
            modified_results = [self._calc_modifier(item, command.modifier, command.roll_operation)
                                for item in raw_results]
            logging.debug('Dicebot modified results: {}'.format(modified_results))
        else:
            modified_results = raw_results
            logging.debug('No modifier applied.')
        return modified_results

    @staticmethod
    def _calc_modifier(value, modifier, roll_operation):
        logging.debug('Detecting modifier...')
        if roll_operation == ADD:
            modified_value = value + modifier
            logging.debug('Adding modifier.')
        elif roll_operation == SUBTRACT:
            modified_value = value - modifier
            logging.debug('Subtracting modifier.')
        else:
            raise DiceRollError("Unsupported modifier type received. Modifier sign: {}".format(roll_operation))
        logging.debug('Returning modified results.')
        return modified_value


class Command:
    def __init__(self, num_dice, num_sides, modifier, roll_operation, raw_command):
        self.num_dice = num_dice
        self.num_sides = num_sides
        self.modifier = modifier
        self.roll_operation = roll_operation
        self.raw_command = raw_command


class DiceResults:
    def __init__(self, raw_rolls, modified_rolls, command):
        self.raw_rolls = raw_rolls
        self.modified_rolls = modified_rolls
        self.command = command

    def __str__(self):
        raw_rolls_for_msg = [str(item) for item in self.raw_rolls]
        mod_rolls_for_msg = [str(item) for item in self.modified_rolls]
        result_msg = "Roll: {command}\nResult: {res}\nUnmodified: {res_raw}".format(
            command=self.command.raw_command,
            res=",".join(mod_rolls_for_msg),
            res_raw="({})".format(','.join(raw_rolls_for_msg))
        )
        return result_msg
