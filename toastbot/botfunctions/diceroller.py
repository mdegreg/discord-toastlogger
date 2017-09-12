"""
Dicebot functionality
"""
import random
import re

ADD = "+"
SUBTRACT = "-"
DEFAULT_MAX_DICE = 100
DEFAULT_MAX_SIDES = 1000
DEFAULT_MAX_MODIFIER = 1000


class DiceRollCommandError(ValueError):
    pass


class DiceRollFormatError(ValueError):
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

    def parse_command(self, raw_command):
        print(self._command_parsing_regex)
        print(raw_command)
        result = re.match(self._command_parsing_regex, raw_command)
        if result is None:
            raise DiceRollFormatError("Regex failed to match command. Command: {}".format(raw_command))
        else:
            #  Group 0 is the entire match.
            num_dice = int(result.group(1))
            print(num_dice)
            num_sides = int(result.group(2))
            print(num_sides)
            operation_sign = result.group(3) if result.group(3) else None
            print(operation_sign)
            modifier = int(result.group(4)) if result.group(4) else None
            print(modifier)
            command = Command(num_dice, num_sides, modifier, operation_sign, raw_command)
            self._validate_command(command)
            return command

    def _validate_command(self, command):
        if command.modifier is not None and command.modifier > self.config.max_modifier:
            exception_msg = "Error: Specified roll modifier is too large. Requested: {}, maximum is {}.".format(
                command.modifier, self.config.max_modifier
            )
            raise DiceRollCommandError(exception_msg)
        elif command.roll_operation is not None and command.roll_operation not in self.config.permitted_operations:
            #  Provide standard initial output string for error.
            exception_msg = "Error: Specified modifier operation is unsupported.\nSupported operations: {}".format(
                self.config.permitted_operations
            )
            raise DiceRollCommandError(exception_msg)

        elif command.num_dice > self.config.max_num_dice:
            exception_msg = "Error: Specified number of dice is too large. Requested: {}, maximum is {}.".format(
                command.num_dice, self.config.max_num_dice
            )
            raise DiceRollCommandError(exception_msg)
        elif command.num_sides > self.config.max_num_sides:
            exception_msg = "Error: Specified size of dice is too large. Requested: {}, maximum is {}.".format(
                command.num_sides, self.config.max_num_sides
            )
            raise DiceRollCommandError(exception_msg)
        else:
            #  Below statement is for explicitness.
            pass


class Dicebot:
    """
    Bot to provide dice rolls on request.
    """
    MIN_NUM_SIDES_ON_DICE = 1

    def __init__(self, command_parser=CommandParser()):
        self.command_parser = command_parser

    def set_seed(self, value):
        random.seed(value)
        return "Dicebot seed set to {}".format(value)

    def roll(self, raw_command):
        command = self.command_parser.parse_command(raw_command)
        raw_results = self._roll_dice(command)
        modified_results = self._apply_modifier(raw_results, command)
        results = DiceResults(raw_results, modified_results, command)
        return results

    @staticmethod
    def _roll_dice(command):
        #  List comprehension to generate random numbers for each desired die.
        raw_results = [random.randint(Dicebot.MIN_NUM_SIDES_ON_DICE, command.num_sides)
                       for i in range(command.num_dice)]
        return raw_results

    def _apply_modifier(self, raw_results, command):
        if command.modifier is not None:
            modified_results = [self._calc_modifier(item, command.modifier, command.roll_operation)
                                for item in raw_results]
        else:
            modified_results = raw_results
        return modified_results

    @staticmethod
    def _calc_modifier(value, modifier, roll_operation):
        if roll_operation == ADD:
            modified_value = value + modifier
        elif roll_operation == SUBTRACT:
            modified_value = value - modifier
        else:
            raise DiceRollCommandError("Unsupported modifier type received. Modifier sign: {}".format(roll_operation))
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
