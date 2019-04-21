import inspect
# Define a custom logger to make terminal logs easier to parse
# TODO: Create option to writes logs to file


# Terminal colors
class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


DEBUG_FLAG = False


class logger:
    @staticmethod
    def log(message):
        print(f'Log       {message}')
        # print(f'/\/\/\/\/\| {message}')

    @staticmethod
    def error(message):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        print(f'{TerminalColors.FAIL}Error     {message}{TerminalColors.ENDC}')
        print(f'{TerminalColors.FAIL}              File     : {info.filename}{TerminalColors.ENDC}')
        print(f'{TerminalColors.FAIL}              Function : {info.function}{TerminalColors.ENDC}')
        print(f'{TerminalColors.FAIL}              Line     : {info.lineno}{TerminalColors.ENDC}')

    @staticmethod
    def warn(message):
        print(f'{TerminalColors.WARNING}Warning   {message}{TerminalColors.ENDC}')

    @staticmethod
    def debug(message):
        if DEBUG_FLAG:
            print(f'Debug     {message}')

    @staticmethod
    def info(message):
        print(f'{TerminalColors.UNDERLINE}Info      {message}{TerminalColors.ENDC}')
