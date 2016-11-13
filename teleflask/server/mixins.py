# -*- coding: utf-8 -*-
import logging
from pytgbot.api_types.receivable.updates import Update

from .base import TeleflaskMixinBase

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class UpdateListenersMixin(TeleflaskMixinBase):
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
    """
    update_listeners = list()

    def on_update(self, func):
        """
        Decorator to register a function to receive updates.

        Usage:
            >>> @app.on_update
            >>> def foo(update):
            >>>     assert isinstance(update, Update)
            >>>     # do stuff with the update
            >>>     # you can use app.bot to access the bot's messages functions
        """
        self.add_update_listener(func)
        return func
    # end def

    def add_update_listener(self, func):
        if func not in self.update_listeners:
            self.update_listeners.append(func)
        else:
            logger.warning("listener already added.")
        # end if
        return func
    # end def

    def remove_update_listener(self, func):
        if func in self.update_listeners:
            self.update_listeners.remove(func)
        else:
            logger.warning("listener already removed.")
        # end if
        return func
    # end def

    def process_update(self, update):
        """
        Iterates through self.update_listeners, and calls them with (update, app).

        No try catch stuff is done, will fail instantly, and not process any remaining listeners.

        :param update:
        :return: the last non-None result any listener returned.
        """
        for listener in self.update_listeners:
            try:
                self.process_result(update, listener(update))
            except Exception:
                logger.exception("Error executing the update listener {func}.".format(func=listener))
            # end if
        # end for
        super().process_update(update)
    # end def

    def do_startup(self):
        super().do_startup()
    # end if
# end class


class BotMessagesMixin(TeleflaskMixinBase):
    """
    Add this to get messages.

    After adding this mixin to the TeleflaskBase you will get:

    `add_message_listener` to add functions
    `remove_message_listener` to remove them again.
    `@on_message` decorator as alias to `_message_listener`

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

        >>> @app.on_message("command")
        >>> def foobar(update, msg):
        >>>     ...  # like above
    """
    message_listeners = list()

    def on_message(self, function):
        """
        Decorator to register a listener for a message event.

        Usage:
            >>> @app.on_command("foo")
            >>> def foo(update, text):
            >>>     assert isinstance(update, Update)
            >>>     app.bot.send_message(update.message.chat.id, "bar:" + text)

            If you now write "/foo hey" to the bot, it will reply with "bar:hey"

        @on_command decorator. Actually is an alias to @command.
        :param command: the string of a command
        """
        self.add_message_listener(function)
        return function
    # end if

    def add_message_listener(self, function):
        """
        Adds an listener for updates with messages.
        No error will be raised if it is already registered. In that case a warning will be logged, but noting else will happen.

        :param function:  The function to call. Will be called with the update and the message as arguments
        :return: the function, unmodified
        """
        if function not in self.message_listeners:
            self.message_listeners.append(function)
        else:
            logger.warning("listener already added.")
        # end if
        return function
        # end for
    # end def add_command


    def remove_update_listener(self, func):
        """
        Removes an function from the message update listener list.
        No error will be raised if it is already registered. In that case a warning will be logged, but noting else will happen.


        :param function:  The function to remove
        :return: the function, unmodified
        """
        if func in self.message_listeners:
            self.message_listeners.remove(func)
        else:
            logger.warning("listener already removed.")
        # end if
        return func
    # end def

    def process_update(self, update):
        """
        Iterates through self.message_listeners, and calls them with (update, app).

        No try catch stuff is done, will fail instantly, and not process any remaining listeners.

        :param update:
        :return: the last non-None result any listener returned.

        :param update: incoming telegram update.
        :return: nothing.
        """
        assert isinstance(update, Update)
        if update.message:
            for listener in self.message_listeners:
                try:
                    self.process_result(update, listener(update, update.message))
                except Exception:
                    logger.exception("Error executing the update listener {func}.".format(func=listener))
                # end try
            # end for
        # end if
        super().process_update(update)
        # end def
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

