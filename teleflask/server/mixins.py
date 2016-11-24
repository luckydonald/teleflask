# -*- coding: utf-8 -*-
import logging
from pytgbot.api_types.receivable.updates import Update

from .base import TeleflaskMixinBase

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class UpdatesMixin(TeleflaskMixinBase):
    """
    This mixin allows you to register functions to listen on updates.

    Functions added to your app:

     `@app.on_update` decorator
     `app.add_update_listener(func)`
     `app.remove_update_listener(func)`

    The registered function will be called with an `pytgbot.api_types.receivable.updates.Update` update parameter.

     So you could use it like this:

     >>> @app.on_update
     >>> def foobar(update):
     >>>     assert isinstance(update, pytgbot.api_types.receivable.updates.Update)
     >>>     pass

     Also you can filter out Updates by specifying which attributes must be non-empty, like this:

     >>> @app.on_update("inline_query")
     >>> def foobar2(update):
     >>>     assert update.inline_query
     >>>     # only get inline queries.

    """
    update_listeners = dict()

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
            self.add_update_listener(function, required_keywords=required_keywords)
        # end def
        if (len(required_keywords)==1 and  # given could be the function, or a single required_keyword.
            not isinstance(required_keywords[0], str) # not string -> must be function
             ):
            # @on_update
            return on_update_inner(function=required_keywords[0])  # not string -> must be function
        # end if
        # -> else: *required_keywords are the strings
        # @on_update("update_id", "message", "whatever")
        return on_update_inner  # let that function be called again with the function.
    # end def

    def add_update_listener(self, function, required_keywords=None):
        """
        Adds an listener for updates.
        You can filter them if you supply a list of names of attributes which all need to be present.
        No error will be raised if it is already registered. In that case a warning will be logged,
        but nothing else will happen, and the function is not added.

        Examples:
            >>> add_update_listener(func, required_keywords=["update_id", "message"])
            # will call  func(msg)  for all updates which are message (have the message attribute) and have a update_id.

            >>> add_message_listener(func, required_keywords=["inline_query"])
            # calls   func(msg)     for all updates which are inline queries (have the inline_query attribute)

            >>> add_message_listener(func)
            # allows all messages.

        :param function:  The function to call. Will be called with the update and the message as arguments
        :param required_keywords: If that evaluates to False (None, empty list, etc...) the filter is not applied, all messages are accepted.
                                  Must be a list.
        :return: the function, unmodified
        """
        # checking input.
        if not required_keywords:
            required_keywords = []
        elif isinstance(required_keywords, tuple):
            required_keywords = list(required_keywords)
        # end if
        assert isinstance(required_keywords, list)
        for keyword in required_keywords:
            assert isinstance(keyword, str)  # required_keywords must all be type str
        # end if

        # checking if already exists.
        if function not in self.update_listeners:
            self.update_listeners[function] = required_keywords
        else:
            logger.warning("listener already added.")
        # end if
        return function
    # end def add_update_listenner

    def remove_update_listener(self, func):
        """
        Removes an function from the update listener list.
        No error will be raised if it is already registered. In that case a warning will be logged,
        but noting else will happen.


        :param function:  The function to remove
        :return: the function, unmodified
        """
        if func in self.update_listeners:
           del self.update_listeners[func]
        else:
            logger.warning("listener already removed.")
        # end if
        return func
    # end def

    def process_update(self, update):
        """
        Iterates through self.update_listeners, and calls them with (update, app).

        No try catch stuff is done, will fail instantly, and not process any remaining listeners.

        :param update: incoming telegram update.
        :return: nothing.
        """
        assert isinstance(update, Update)
        for listener, required_fields in self.update_listeners.items():
            try:
                if not required_fields or all([hasattr(update, f) and getattr(update, f) for f in required_fields]):
                    # either filters evaluates to False, (None, empty list etc) which means it should not filter
                    # or it has filters, than we need to check if that attributes really exist.
                    self.process_result(update, listener(update))
                # end if
            except Exception:
                logger.exception("Error executing the update listener {func}.".format(func=listener))
            # end try
        # end for
        super().process_update(update)
    # end def process_update

    def do_startup(self):
        super().do_startup()
    # end def
# end class


class MessagesMixin(TeleflaskMixinBase):
    """
    Add this to get messages.

    After adding this mixin to the TeleflaskBase you will get:

    `add_message_listener` to add functions
    `remove_message_listener` to remove them again.
    `@on_message` decorator as alias to `add_message_listener`

    Example:
        This is the function we got:

        >>> def foobar(update, msg):
        >>>    assert isinstance(update, Update)
        >>>    assert isinstance(msg, Message)

        Now we can add it like this:

        >>> app.add_message_listener(foobar)

        And remove it again:

        >>> app.remove_message_listener()

        You can also use the handy decorator:

        >>> @app.on_message("text")  # all messages where  msg.text  is existent.
        >>> def foobar(update, msg):
        >>>     ...  # like above
        Would be equal to:
        >>> app.add_message_listener(foobar, ["text"])
    """
    message_listeners = dict()

    def on_message(self, *required_keywords):
        """
        Decorator to register a listener for a message event.
        You can give optionally give one or multiple strings. The message will need to have all this elements.
        If you leave them out, you'll get all messages, unfiltered.

        Usage:
            >>> @app.on_message
            >>> def foo(msg):
            >>>     # all messages
            >>>     assert isinstance(msg, Message)
            >>>     app.bot.send_message(msg.chat.id, "you sent any message!")

            >>> @app.on_message("text")
            >>> def foo(msg):
            >>>     # all messages which are text messages (have the text attribute)
            >>>     assert isinstance(msg, Message)
            >>>     app.bot.send_message(msg.chat.id, "you sent text!")

            >>> @app.on_message("photo", "sticker")
            >>> def foo(msg):
            >>>     # all messages which are photos (have the photo attribute) and have a caption
            >>>     assert isinstance(msg, Message)
            >>>     app.bot.send_message(msg.chat.id, "you sent a photo with caption!")


        :params required_keywords: Optionally: Specify attribute the message needs to have.
        """
        def on_message_inner(function):
            self.add_message_listener(function, required_keywords=required_keywords)
        # end def

        if (len(required_keywords)==1 and  # given could be the function, or a single required_keyword.
            not isinstance(required_keywords[0], str) # not string -> must be function
             ):
            # @on_message
            return on_message_inner(function=required_keywords[0])  # not string -> must be function
        # end if
        # -> else: *required_keywords are the strings
        # @on_message("text", "sticker", "whatever")
        return on_message_inner  # let that function be called again with the function.
    # end def

    def add_message_listener(self, function, required_keywords=None):
        """
        Adds an listener for updates with messages.
        You can filter them if you supply a list of names of attributes which all need to be present.
        No error will be raised if it is already registered. In that case a warning will be logged,
        but nothing else will happen, and the function is not added.

        Examples:
            >>> add_message_listener(func, required_keywords=["sticker", "caption"])
            # will call  func(msg)  for all messages which are stickers (have the sticker attribute) and have a caption.

            >>> add_message_listener(func)
            # allows all messages.

        :param function:  The function to call. Will be called with the update and the message as arguments
        :param required_keywords: If that evaluates to False (None, empty list, etc...) the filter is not applied, all messages are accepted.
        :return: the function, unmodified
        """
        # checking input.
        if not required_keywords:
            required_keywords = []
        elif isinstance(required_keywords, tuple):
            required_keywords = list(required_keywords)
        # end if
        assert isinstance(required_keywords, list)
        for keyword in required_keywords:
            assert isinstance(keyword, str)  # required_keywords must all be type str
        # end if

        # checking if already exists.
        if function not in self.message_listeners:
            self.message_listeners[function] = required_keywords
        else:
            logger.warning("listener already added.")
        # end if
        return function
        # end for
    # end def add_command

    def remove_message_listener(self, func):
        """
        Removes an function from the message listener list.
        No error will be raised if it is already registered. In that case a warning will be logged,
        but noting else will happen.


        :param function:  The function to remove
        :return: the function, unmodified
        """
        if func in self.message_listeners:
            del self.message_listeners[func]
        else:
            logger.warning("listener already removed.")
        # end if
        return func
    # end def

    def process_update(self, update):
        """
        Iterates through self.message_listeners, and calls them with (update, app).

        No try catch stuff is done, will fail instantly, and not process any remaining listeners.

        :param update: incoming telegram update.
        :return: nothing.
        """
        assert isinstance(update, Update)
        if update.message:
            msg = update.message
            for listener, required_fields in self.message_listeners.items():
                try:
                    if not required_fields or all([hasattr(msg, f) and getattr(msg, f) for f in required_fields]):
                        # either filters evaluates to False, (None, empty list etc) which means it should not filter
                        # or it has filters, than we need to check if that attributes really exist.
                        self.process_result(update, listener(update.message))
                    # end if
                except Exception:
                    logger.exception("Error executing the update listener {func}.".format(func=listener))
                # end try
            # end for
        # end if
        super().process_update(update)
    # end def process_update

    def do_startup(self):
        super().do_startup()
    # end def
# end class


class BotCommandsMixin(TeleflaskMixinBase):
    """
    Add this to get commands.

    After adding this mixin to the TeleflaskBase you will get:

    `add_command` to add functions
    `remove_command` to remove them again.
    `@command` decorator as alias to `add_command`
    `@on_command` decorator as alias to `@command`

    Example:
        This is the function we got:

        >>> def foobar(update, text):
        >>>    assert isinstance(update, Update)
        >>>    text_to_send = "Your command has"
        >>>    text_to_send += "no argument." if text is None else ("the following args: " + text)
        >>>    app.bot.send_message(update.message.chat.id, text=text_to_send)

        Now we can add it like this:

        >>> app.add_command("command", foobar)

        And remove it again:

        >>> app.remove_command(command="command")
        or
        >>> app.remove_command(function=foobar)

        You can also use the handy decorator:

        >>> @app.command("command")
        >>> def foobar(update, text):
        >>>     ...  # like above
    """
    commands = dict()

    def on_command(self, command):
        """
        Decorator to register a command.

        Usage:
            >>> @app.on_command("foo")
            >>> def foo(update, text):
            >>>     assert isinstance(update, Update)
            >>>     app.bot.send_message(update.message.chat.id, "bar:" + text)

            If you now write "/foo hey" to the bot, it will reply with "bar:hey"

        @on_command decorator. Actually is an alias to @command.
        :param command: the string of a command
        """
        return self.command(command)
    # end if

    def command(self, command):
        """
        Decorator to register a command.

        Usage:
            >>> @app.command("foo")
            >>> def foo(update, text):
            >>>     assert isinstance(update, Update)
            >>>     app.bot.send_message(update.message.chat.id, "bar:" + text)

            If you now write "/foo hey" to the bot, it will reply with "bar:hey"

        :param command: the string of a command
        """
        def register_command(func):
            self.add_command(command, func)
            return func
        return register_command
    # end def

    def add_command(self, command, function):
        """
        Adds `/command` and `/command@bot`
        (also the iOS urls `command:///command` and `command:///command@bot`)

        Will overwrite existing commands.

        Arguments to the functions decorated will be (update, text)
            - update: The update from telegram. :class:`pytgbot.api_types.receivable.updates.Update`
            - text: The text after the command (:class:`str`), or None if there was no text.
        Also see :def:`BotCommandsMixin._execute_command()`

        :param command: The command
        :param function:  The function to call. Will be called with the update and the text after the /command as args.
        :return: Nothing
        """
        for cmd in self._yield_commands(command):
            self.commands[cmd] = function
        # end for
    # end def add_command

    def remove_command(self, command=None, function=None):
        if command:
            for cmd in self._yield_commands(command):
                if cmd not in self.commands:
                    continue
                # end if
                del self.commands["cmd"]
            # end for
        # end if
        if function:
            for key, value in self.commands.items():
                if value == function:
                    del self.commands[key]
                # end if
            # end for
        # end if
        if not command and not function:
            raise ValueError("You have to specify a command or a function to remove. Or both.")
        # end if
    # end def remove_command

    def process_update(self, update):
        """
        If the message is a registered command it will be called.
        Arguments to the functions will be (update, text)
            - update: The :class:`pytgbot.api_types.receivable.updates.Update`
            - text: The text after the command, or None if there was no text.
        Also see ._execute_command()

        :param update: incoming telegram update.
        :return: nothing.
        """
        assert isinstance(update, Update)
        if update.message and update.message.text:
            txt = update.message.text.strip()
            if txt in self.commands:
                logger.debug("Running command {input}.".format(input=txt))
                self._execute_command(self.commands[txt], update, txt, None)
            elif " " in txt and txt.split(" ")[0] in self.commands:
                cmd, text = tuple(txt.split(" ", maxsplit=1))
                logger.debug("Running command {cmd} ({input!r}).".format(cmd=cmd, input=txt))
                self._execute_command(self.commands[cmd], update, cmd, text.strip())
            # end if
        # end if
        super().process_update(update)
    # end def process_update

    def do_startup(self):
        super().do_startup()
    # end if

    def _execute_command(self, func, update, command, text):
        try:
            self.process_result(update, func(update, text))
        except Exception:
            logger.exception("Failed calling command {cmd!r} ({func}):".format(cmd=command, func=func))
        # end try
    # end def

    def _yield_commands(self, command):
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
            yield syntax.format(command=command, username=self.username)
        # end for
    # end def _yield_commands
# end class


class StartupMixin(TeleflaskMixinBase):
    """
    This mixin allows you to register functions to be run on bot/server start.

        Functions added to your app:

         `@app.on_update` decorator
         `app.add_update_listener(func)`
         `app.remove_update_listener(func)`

        The registered function will be called on either the server start, or as soon as registered.

         So you could use it like this:

         >>> @app.on_update
         >>> def foobar(update):
         >>>     assert isinstance(update, pytgbot.api_types.receivable.updates.Update)
         >>>     pass
        """
    startup_listeners = list()
    startup_already_run = False

    def on_startup(self, func):
        """
        Decorator to register a function to receive updates.

        Usage:
            >>> @app.on_startup
            >>> def foo():
            >>>     print("doing stuff on boot")

        """
        self.add_startup_listener(func)
        return func
    # end def

    def add_startup_listener(self, func):
        if func not in self.startup_listeners:
            self.startup_listeners.append(func)
            if self.startup_already_run:
                func()
            # end if
        else:
            logger.warning("listener already added.")
        # end if
        return func
    # end def

    def remove_startup_listener(self, func):
        if func in self.startup_listeners:
            self.startup_listeners.remove(func)
        else:
            logger.warning("listener already removed.")
        # end if
        return func
    # end def

    def do_startup(self):
        """
        Iterates through self.startup_listeners, and calls them.

        No try catch stuff is done, will fail instantly, and not process any remaining listeners.

        :param update:
        :return: the last non-None result any listener returned.
        """
        for listener in self.startup_listeners:
            try:
                listener()
            except Exception:
                logger.exception("Error executing the startup listener {func}.".format(func=listener))
                raise
            # end if
        # end for
        self.startup_already_run = True
        super().do_startup()
    # end def

    def process_update(self, update):
        super().process_update(update)
    # end if
# end class

