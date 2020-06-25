#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from typing import Callable, Union, List, Tuple, Type, Any

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

from pytgbot.api_types.receivable.updates import Update, Message
from ..messages import Message as OldSendableMessage
from ..new_messages import SendableMessageBase

SENDABLE_MESSAGE_TYPES = Union[OldSendableMessage, SendableMessageBase]
OPTIONAL_SENDABLE_MESSAGE_TYPES = Union[None, SENDABLE_MESSAGE_TYPES]
class DEFAULT: pass

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class NoMatch(Exception):
    """
    Raised by a filter if it denies to process the update.
    """
    pass
# end def


class Filter(object):
    DEFAULT_CALLABLE = Callable[[Update], OPTIONAL_SENDABLE_MESSAGE_TYPES]  # self.func(update) -> OPTIONAL_SENDABLE_MESSAGE_TYPES
    MATCH_RESULT_TYPE = Union[bool, None, Any]

    type: str
    func: Union[Callable, DEFAULT_CALLABLE]

    def __init__(self, type: str, func: Union[Callable, DEFAULT_CALLABLE]):
        """
        :param type: The type of this class.
        :param func: The function registered.
        """
        self.type = type
        self.func = func
    # end def

    @abstractmethod
    def match(self, update: Update) -> MATCH_RESULT_TYPE:
        return True
    # end def

    @abstractmethod
    def call_handler(self, update: Update, match_result: MATCH_RESULT_TYPE) -> OPTIONAL_SENDABLE_MESSAGE_TYPES:
        """
        Calls the callback
        """
        return self.func(update)
    # end def
# end class


class UpdateFilter(Filter):
    """
    Filter for update types.

    >>> @bot.on_update
    ... def foo(update):
    ...     pass
    ... # end def

    >>> @bot.on_update('message')
    ... def foo(update):
    ...     pass
    ... # end def

    >>> @bot.on_update(required_update_keywords=['message'])
    ... def foo(update):
    ...     pass
    ... # end def

    """
    TYPE = 'update'
    MATCH_RESULT_TYPE = None

    required_update_keywords: Union[List[str], None]

    def __init__(self, func: Callable, required_update_keywords: Union[List[str], None] = None):
        super().__init__(self.TYPE, func=func)
        self.required_update_keywords = self._prepare_required_keywords(required_update_keywords)
    # end def

    @staticmethod
    def _prepare_required_keywords(required_keywords: Union[str, List[str], Tuple[str, ...]]) -> List[str]:
        # check input, make a list out of what we might get.
        if isinstance(required_keywords, str):
            required_keywords = [required_keywords]  # str => [str]
        elif isinstance(required_keywords, tuple):
            required_keywords = list(required_keywords)  # (str,str) => [str,str]
        # end if
        assert isinstance(required_keywords, list)
        for keyword in required_keywords:
            assert isinstance(keyword, str)  # required_update_keywords must all be type str
        # end if
        return required_keywords
    # end def

    def match(self, update: Update, required_keywords: Union[Type[DEFAULT], None, List[str]] = DEFAULT) -> MATCH_RESULT_TYPE:
        if required_keywords == DEFAULT:
            required_keywords = self.required_update_keywords
        # end if

        if required_keywords is None:
            # no filter -> allow all the differnt type of updates
            return
        # end if

        if all(getattr(update, required_keyword, None) != None for required_keyword in required_keywords):
            # we have one of the required fields
            return
        # end if
        raise NoMatch('update not matching the required keywords')
    # end def

    def call_handler(self, update: Update, match_result: MATCH_RESULT_TYPE) -> OPTIONAL_SENDABLE_MESSAGE_TYPES:
        """
        Calls the callback
        """
        return self.func(update)
    # end def
# end def


class MessageFilter(UpdateFilter):
    """
    You can give optionally give one or multiple strings. The message will need to have all this elements.
    If you leave them out, you'll get all messages, unfiltered.

    Usage:
        >>> @app.on_message
        >>> def foo(update, msg):
        >>>     # all messages
        >>>     assert isinstance(update, Update)
        >>>     assert isinstance(msg, OldSendableMessage)
        >>>     app.bot.send_message(msg.chat.id, "you sent any message!")

        >>> @app.on_message("text")
        >>> def foo(update, msg):
        >>>     # all messages which are text messages (have the text attribute)
        >>>     assert isinstance(update, Update)
        >>>     assert isinstance(msg, OldSendableMessage)
        >>>     app.bot.send_message(msg.chat.id, "you sent text!")

        >>> @app.on_message("photo", "caption")
        >>> def foo(update, msg):
        >>>     # all messages which are photos (have the photo attribute) and have a caption (text)
        >>>     assert isinstance(update, Update)
        >>>     assert isinstance(msg, OldSendableMessage)
        >>>     app.bot.send_message(msg.chat.id, "you sent a photo with caption!")

    :params required_update_keywords: Optionally: Specify attribute the message needs to have.
    """
    MATCH_RESULT_TYPE = None
    func: Union[Callable, Callable[[Update, Message], OPTIONAL_SENDABLE_MESSAGE_TYPES]]

    def __init__(self, func: Union[Callable, Callable[[Update, Message], OPTIONAL_SENDABLE_MESSAGE_TYPES]], required_update_keywords: Union[List[str], None] = None):
        super().__init__(func=func, required_update_keywords=['message'])
        self.required_message_keywords = self._prepare_required_keywords(required_update_keywords)
    # end def

    def match(self, update: Update, required_keywords: Union[Type[DEFAULT], None, List[str]] = DEFAULT) -> MATCH_RESULT_TYPE:
        super().match(update=update, required_keywords=['message'])

        if required_keywords == DEFAULT:
            required_keywords = self.required_message_keywords
        # end if

        if required_keywords is None:
            # no filter -> allow all the differnt type of updates
            return
        # end if

        if all(getattr(update.message, required_keyword, None) != None for required_keyword in required_keywords):
            # we have one of the required fields
            return
        # end if
        raise NoMatch('message not matching the required keywords')
    # end def

    def call_handler(self, update: Update, match_result: MATCH_RESULT_TYPE) -> OPTIONAL_SENDABLE_MESSAGE_TYPES:
        """
        Calls the callback
        """
        message = update.message
        return self.func(update, message)
    # end def
# end class


class CommandFilter(MessageFilter):
    """
    Add this to get commands.

    Usage:
        >>> @app.command("command")
        >>> def foobar(update, text):
        >>>     ...  # like above
    """
    TEXT_PARAM_TYPE = Union[None, str]
    MATCH_RESULT_TYPE = TEXT_PARAM_TYPE

    func: Union[Callable, Callable[[Update, Union[str, None]], OPTIONAL_SENDABLE_MESSAGE_TYPES]]

    command: str
    _command: str

    username: str
    _username: str

    command_strings: Tuple[str, ...]
    _command_strings: Union[Tuple[str, ...], None]

    def __init__(self, func: Union[Callable, Callable[[Update, Message], OPTIONAL_SENDABLE_MESSAGE_TYPES]], command: str, username: str):
        super().__init__(func=func, required_update_keywords=['message'])
        self._command = command
        self._username = username
        self._command_strings = tuple(self._yield_commands(command=command, username=username))
    # end def

    @property
    def command(self) -> str:
        return self._command
    # end def

    @command.setter
    def command(self, value: str):
        self._command = value
        self._command_strings = tuple(self._yield_commands(command=value, username=self._username))
    # end def

    @property
    def username(self) -> str:
        return self._username
    # end def

    @username.setter
    def username(self, value: str):
        self._username = value
        self._command_strings = tuple(self._yield_commands(command=self._command, username=value))
    # end def

    @property
    def command_strings(self) -> Tuple[str, ...]:
        if self._command_strings is None:
            self._command_strings = tuple(self._yield_commands(command=self._command, username=self._username))
        # end if
        return self._command_strings
    # end def

    @staticmethod
    def _yield_commands(command, username):
        """
        Yields possible strings with the given commands.
        Like `/command` and `/command@bot`.

        :param command: The command to construct.
        :return:
        """
        for syntax in (
                "/{command}",  # without username
                "/{command}@{username}",  # with username
                "command:///{command}",  # iOS represents commands like this
                "command:///{command}@{username}"  # iOS represents commands like this
        ):
            yield syntax.format(command=command, username=username)
        # end for
    # end def _yield_commands

    def match(self, update: Update, required_keywords: Union[Type[DEFAULT], None, List[str]] = DEFAULT) -> MATCH_RESULT_TYPE:
        if not super().match(update=update, required_keywords=['text']):
            return None
        # end if

        txt = update.message.text.strip()
        if txt in self._command_strings:
            logger.debug(f"got command {txt} (no text).")
            return None
        elif " " in txt and txt.split(" ")[0] in self._command_strings:
            cmd, text = tuple(txt.split(" ", maxsplit=1))
            logger.debug(f"got command {cmd} (text={text!r}).")
            return text
        else:
            raise NoMatch('did not match the command')
        # end if
    # end def

    def call_handler(self, update: Update, match_result: MATCH_RESULT_TYPE) -> OPTIONAL_SENDABLE_MESSAGE_TYPES:
        """
        Calls the callback
        """
        return self.func(update, text=match_result)
    # end def
# end class


class FilterHolder(object):
    def on_update(self, *required_keywords):
        """
        Decorator to register a function to receive updates.

        Usage:
            >>> @app.on_update
            >>> def foo(update):
            >>>     assert isinstance(update, Update)
            >>>     # do stuff with the update
            >>>     # you can use app.bot to access the bot's messages functions
        """
        def on_update_inner(function):
            return self.add_update_listener(function, required_keywords=required_keywords)
        # end def
        if (
            len(required_keywords) == 1 and  # given could be the function, or a single required_keyword.
            not isinstance(required_keywords[0], str)  # not string -> must be function
        ):
            # @on_update
            function = required_keywords[0]
            required_keywords = None
            return on_update_inner(function)  # not string -> must be function
        # end if
        # -> else: *required_update_keywords are the strings
        # @on_update("update_id", "message", "whatever")
        return on_update_inner  # let that function be called again with the function.
    # end def
