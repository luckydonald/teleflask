# -*- coding: utf-8 -*-
import logging
from abc import abstractmethod
from collections import OrderedDict
from typing import List

from pytgbot.api_types.receivable.updates import Update

from .filters import UpdateFilter, Filter, NoMatch, MessageFilter, CommandFilter
from ..exceptions import AbortProcessingPlease
from .abstact import AbstractUpdates, AbstractBotCommands, AbstractMessages, AbstractRegisterBlueprints, AbstractStartup
from .base import TeleflaskMixinBase

__author__ = 'luckydonald'
__all__ = ['RegisterBlueprintsMixin', 'StartupMixin', 'UpdatesMixin']
logger = logging.getLogger(__name__)


class UpdatesMixin(TeleflaskMixinBase, AbstractUpdates):
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
    def __init__(self, *args, **kwargs):
        self.update_listeners: List[Filter] = []

        super(UpdatesMixin, self).__init__(*args, **kwargs)
    # end def

    on_update = UpdateFilter.decorator
    on_update.__doc__ = """
        Decorator to register a function to receive updates.

        Usage:
            >>> @app.on_update
            >>> def foo(update):
            >>>     assert isinstance(update, Update)
            >>>     # do stuff with the update
            >>>     # you can use app.bot to access the bot's messages functions

        :params required_keywords: Optionally: Specify attribute the message needs to have.
    """

    on_message = MessageFilter.decorator
    on_message.__doc__ = """
        Decorator to register a listener for a message event.
        You can give optionally give one or multiple strings. The message will need to have all this elements.
        If you leave them out, you'll get all messages, unfiltered.

        Usage:
            >>> @app.on_message
            >>> def foo(update, msg):
            >>>     # all messages
            >>>     assert isinstance(update, Update)
            >>>     assert isinstance(msg, Message)
            >>>     app.bot.send_message(msg.chat.id, "you sent any message!")

            >>> @app.on_message("text")
            >>> def foo(update, msg):
            >>>     # all messages which are text messages (have the text attribute)
            >>>     assert isinstance(update, Update)
            >>>     assert isinstance(msg, Message)
            >>>     app.bot.send_message(msg.chat.id, "you sent text!")

            >>> @app.on_message("photo", "sticker")
            >>> def foo(update, msg):
            >>>     # all messages which are photos (have the photo attribute) and have a caption
            >>>     assert isinstance(update, Update)
            >>>     assert isinstance(msg, Message)
            >>>     app.bot.send_message(msg.chat.id, "you sent a photo with caption!")


        :params required_keywords: Optionally: Specify attribute the message needs to have.
    """

    on_command = CommandFilter.decorator
    on_command.__doc__ = """
        Decorator to register a command.

        Usage:
            >>> @app.command("foo")
            >>> def foo(update, text):
            >>>     assert isinstance(update, Update)
            >>>     app.bot.send_message(update.message.chat.id, "bar:" + text)

            If you now write "/foo hey" to the bot, it will reply with "bar:hey"

        :param command: the string of a command
    """
    command = on_command
    command.__doc__ = "Alias of @on_command:\n\n" + on_command.__doc__

    def register_handler(self, event_handler: Filter):
        """
        Adds an listener for any update type.
        You provide a Filter for them as parameter, it also contains the function.
        No error will be raised if it is already registered. In that case a warning will be logged,
        but nothing else will happen, and the function is not added.

        Examples:
            >>> register_handler(UpdateFilter(func, required_keywords=["update_id", "message"]))
            # will call  func(msg)  for all updates which are message (have the message attribute) and have a update_id.

            >>> register_handler(UpdateFilter(func, required_keywords=["inline_query"]))
            # calls   func(msg)     for all updates which are inline queries (have the inline_query attribute)

            >>> register_handler(UpdateFilter(func, required_keywords=None))
            >>> register_handler(UpdateFilter(func))
            # allows all messages.

        :param function:  The function to call. Will be called with the update and the message as arguments
        :param required_keywords: If that evaluates to False (None, empty list, etc...) the filter is not applied, all messages are accepted.
                                  Must be a list.
        :return: the function, unmodified
        """

        logging.debug("adding handler to listeners")
        self.update_listeners.append(event_handler)  # list of lists. Outer list = OR, inner = AND
        return event_handler
    # end def add_update_listener

    def remove_update_listener(self, event_handler):
        """
        Removes an function from the update listener list.
        No error will be raised if it is already registered. In that case a warning will be logged,
        but noting else will happen.


        :param function:  The function to remove
        :return: the function, unmodified
        """
        try:
            self.update_listeners.remove(event_handler)
        except ValueError:
            logger.warning("listener already removed.")
        # end if
    # end def

    def process_update(self, update):
        """
        Iterates through self.update_listeners, and calls them with (update, app).

        No try catch stuff is done, will fail instantly, and not process any remaining listeners.

        :param update: incoming telegram update.
        :return: nothing.
        """
        assert isinstance(update, Update)  # Todo: non python objects
        filter: Filter
        for filter in self.update_listeners:
            try:
                # check if the Filter matches
                match_result = filter.match(update)
                # call the handler
                result = filter.call_handler(update=update, match_result=match_result)
                # send the message
                self.process_result(update, result)  # this will be TeleflaskMixinBase.process_result()
            except NoMatch as e:
                logger.debug(f'not matching filter {filter!s}.')
            except AbortProcessingPlease as e:
                logger.debug('Asked to stop processing updates.')
                if e.return_value:
                    self.process_result(update, e.return_value)  # this will be TeleflaskMixinBase.process_result()
                # end if
                return  # not calling super().process_update(update)
            except Exception:
                logger.exception(f"Error executing the update listener with {filter!s}: {filter!r}")
            # end try
        # end for
        super().process_update(update)
    # end def process_update

    def do_startup(self):  # pragma: no cover
        super().do_startup()
    # end def
# end class


class StartupMixin(TeleflaskMixinBase, AbstractStartup):
    """
    This mixin allows you to register functions to be run on bot/server start.

        Functions added to your app:

         `@app.on_startup` decorator
         `app.add_startup_listener(func)`
         `app.remove_startup_listener(func)`

        The registered function will be called on either the server start, or as soon as registered.

         So you could use it like this:

         >>> @app.on_startup
         >>> def foobar():
         >>>     print("doing stuff on boot")
        """
    def __init__(self, *args, **kwargs):
        self.startup_listeners = list()
        self.startup_already_run = False
        super(StartupMixin, self).__init__(*args, **kwargs)
    # end def

    def on_startup(self, func):
        """
        Decorator to register a function to receive updates.

        Usage:
            >>> @app.on_startup
            >>> def foo():
            >>>     print("doing stuff on boot")

        """
        return self.add_startup_listener(func)
    # end def

    def add_startup_listener(self, func):
        """
        Usage:
            >>> def foo():
            >>>     print("doing stuff on boot")
            >>> app.add_startup_listener(foo)

        :param func:
        :return:
        """
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

    def process_update(self, update):  # pragma: no cover
        super().process_update(update)
    # end if
# end class


class RegisterBlueprintsMixin(TeleflaskMixinBase, AbstractRegisterBlueprints):
    def __init__(self, *args, **kwargs) -> None:
        #: all the attached blueprints in a dictionary by name.  Blueprints
        #: can be attached multiple times so this dictionary does not tell
        #: you how often they got attached.
        #:
        #: .. versionadded:: 2.0.0
        self.blueprints = {}
        self._blueprint_order = []
        super().__init__(*args, **kwargs)
    # end def

    def register_tblueprint(self, tblueprint, **options):
        """Registers a `TBlueprint` on the application.

        .. versionadded:: 2.0.0
        """
        first_registration = False
        if tblueprint.name in self.blueprints:
            assert self.blueprints[tblueprint.name] is tblueprint, \
                'A teleflask blueprint\'s name collision occurred between %r and ' \
                '%r.  Both share the same name "%s".  TBlueprints that ' \
                'are created on the fly need unique names.' % \
                (tblueprint, self.blueprints[tblueprint.name], tblueprint.name)
        else:
            self.blueprints[tblueprint.name] = tblueprint
            self._blueprint_order.append(tblueprint)
            first_registration = True
        tblueprint.register(self, options, first_registration)

    def iter_blueprints(self):
        """Iterates over all blueprints by the order they were registered.

        .. versionadded:: 0.11
        """
        return iter(self._blueprint_order)
    # end def

    @abstractmethod
    def process_update(self, update):
        return super().process_update(update)
    # end def

    @abstractmethod
    def do_startup(self):
        return super().do_startup()
    # end def
# end class
