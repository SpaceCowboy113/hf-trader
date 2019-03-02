from typing import TypeVar, Union
from maybe import Maybe
from logger import logger
import inspect


def get_frame_info(stack):
    callerframerecord = stack
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    return info


class Error(Exception):
    def __init__(self, message):
        info = get_frame_info(inspect.stack()[1])
        self.file = info.filename
        self.function = info.function
        self.line = info.lineno
        self.message = message
        logger.error(message)  # TODO: Move logging into its own function that takes an error


class Warning(Exception):
    def __init__(self, message):
        info = get_frame_info(inspect.stack()[1])
        self.file = info.filename
        self.function = info.function
        self.line = info.lineno
        self.message = message


Ok = TypeVar('Ok')
Result = Union[Ok, Error, Warning]

T = TypeVar('T')


def to_maybe(result: Result[T]) -> Maybe[T]:
    if isinstance(result, Error) or isinstance(result, Warning):
        return None
    return result


# is_okay is not reused in this file to appease the type checker
def is_okay(result: Result[T]) -> bool:
    if isinstance(result, Error) or isinstance(result, Warning):
        return False
    return True


def with_default(default: T, result: Result[T]) -> T:
    if isinstance(result, Error) or isinstance(result, Warning):
        return default
    return result
    # return default if (result) is None else result

# TODO: Implement helper functions like andThen, withDefault, map, map2, etc.
