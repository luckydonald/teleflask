#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, List, Callable, Dict

from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

from pytgbot import Bot
from pytgbot.api_types.receivable.peer import User
from pytgbot.api_types.receivable.updates import Update

from exceptions import AbortProcessingPlease
from server.extras import logger
from server.filters import Filter, NoMatch, UpdateFilter, MessageFilter, CommandFilter
from teleflask import TBlueprint

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

class Teleserver(object):
    """
    This is the core logic.
    You can register a bunch of listeners. Then you have to call `do_startup` and `process_update` and

    You can use:

        Startup:
            - `app.add_startup_listener` to let the given function be called on server/bot startup
            - `app.remove_startup_listener` to remove the given function again
            - `@app.on_startup` decorator which does the same as add_startup_listener.
            See :class:`teleflask.mixins.StartupMixin` for complete information.

        Commands:
            - `app.add_command` to add command functions
            - `app.remove_command` to remove them again.
            - `@app.command("command")` decorator as alias to `add_command`
            - `@app.on_command("command")` decorator as alias to `add_command`
            See :class:`teleflask.mixins.BotCommandsMixin` for complete information.

        Messages:
            - `app.add_message_listener` to add functions
            - `app.remove_message_listener` to remove them again.
            - `@app.on_message` decorator as alias to `add_message_listener`
            See :class:`teleflask.mixins.MessagesMixin` for complete information.

        Updates:
            - `app.add_update_listener` to add functions to be called on incoming telegram updates.
            - `app.remove_update_listener` to remove them again.
            - `@app.on_update` decorator doing the same as `add_update_listener`
            See :class:`teleflask.mixins.UpdatesMixin` for complete information.

    Execution order:

        It will first check for commands (`@command`), then for messages (`@on_message`) and
        finally for update listeners (`@on_update`)

    Functionality is separated into mixin classes. This means you can plug together a class with just the functions you need.
    But we also provide some ready-build cases:
        :class:`teleflask.extras.TeleflaskCommands`, :class:`teleflask.extras.TeleflaskMessages`,
        :class:`teleflask.extras.TeleflaskUpdates` and :class:`teleflask.extras.TeleflaskStartup`.
    """

    __api_key: str
    _bot = Union[Bot, None]
    _me: Union[User, None]
    _return_python_objects: bool

    startup_listeners: List[Callable]
    startup_already_run: bool

    blueprints: Dict[str, TBlueprint]
    _blueprint_order: List[TBlueprint]

    def __init__(
        self, api_key, app=None, blueprint=None, hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
        debug_routes=False, disable_setting_webhook_telegram=None, disable_setting_webhook_route=None,
        return_python_objects=True
    ):
        """
        A new Teleflask object.

        :param api_key: The key for the telegram bot api.
        :type  api_key: str

        :param app: The flask app if you don't like to call :meth:`init_app` yourself.
        :type  app: flask.Flask | None

        :param blueprint: A blueprint, where the telegram webhook (and the debug endpoints, see `debug_routes`) will be registered in.
                          Use if you don't like to call :meth:`init_app` yourself.
                          If not set, but `app` is, it will register any routes to the `app` itself.
                          Note: This is NOT a `TBlueprint` but a regular `flask` one!
        :type  blueprint: flask.Blueprint | None

        :param hostname: The hostname or IP (and maybe a port) where this server is reachable in the internet.
                         Specify the path with :param hostpath:
                         Used to calculate the webhook url.
                         Also configurable via environment variables. See calculate_webhook_url()
        :param hostpath: The host url the base of where this bot is reachable.
                         Examples: None (for root of server) or "/bot2"
                         Note: The webhook will only be set on initialisation.
                         Also configurable via environment variables. See calculate_webhook_url()
        :param hookpath: The endpoint of the telegram webhook.
                        Defaults to "/income/<API_KEY>"
                        Note: The webhook will only be set on initialisation.
                        Also configurable via environment variables. See calculate_webhook_url()
        :param debug_routes: Add extra url endpoints usefull for debugging. See setup_routes(...)

        :param disable_setting_webhook_telegram: Disable updating the telegram webhook when starting.
                                                 Useful for unit tests. Defaults to the app's config
                                                 DISABLE_SETTING_ROUTE_WEBHOOK or False.
        :type  disable_setting_webhook_telegram: None|bool

        :param disable_setting_webhook_route: Disable creation of the webhook route.
                                              Usefull if you don't need to listen for incomming events.
        :type  disable_setting_webhook_route: None|bool

        :param return_python_objects: Enable return_python_objects in pytgbot. See pytgbot.bot.Bot
        """

        self.startup_listeners: List[Callable] = list()
        self.startup_already_run: bool = False

        self.blueprints: Dict[str, TBlueprint] = {}
        self._blueprint_order: List[TBlueprint] = []

        self.__api_key: str = api_key
        self._bot = Union[Bot, None] = None  # will be set in self.init_bot()
        self._me: Union[User, None] = None  # will be set in self.init_bot()
        self._return_python_objects: bool = return_python_objects

        super().__init__(
            api_key=api_key, app=app, blueprint=blueprint, hostname=hostname, hookpath=hookpath,
            debug_routes=debug_routes, disable_setting_webhook_telegram=disable_setting_webhook_telegram,
            disable_setting_webhook_route=disable_setting_webhook_route, return_python_objects=return_python_objects,
        )
        # end def

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
    # end def

    def remove_handler(self, event_handler):
        """
        Removes an handler from the update listener list.
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

    def remove_handled_func(self, func):
        """
        Removes an function from the update listener list.
        No error will be raised if it is no longer registered. In that case noting else will happen.

        :param function:  The function to remove
        :return: the function, unmodified
        """
        listerner: Filter
        self.update_listeners = [listerner for listerner in self.update_listeners if listerner.func != func]
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

    def register_tblueprint(self, tblueprint: TBlueprint, **options):
        """
        Registers a `TBlueprint` on the application.
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
    # end def

    def iter_blueprints(self):
        """
        Iterates over all blueprints by the order they were registered.
        """
        return iter(self._blueprint_order)
    # end def

    def process_result(self, update, result):
        """
        Send the result.
        It may be a :class:`Message` or a list of :class:`Message`s
        Strings will be send as :class:`TextMessage`, encoded as raw text.

        :param update: A telegram incoming update
        :type  update: Update

        :param result: Something to send.
        :type  result: Union[List[Union[Message, str]], Message, str]

        :return: List of telegram responses.
        :rtype: list
        """
        from ..messages import Message
        from ..new_messages import SendableMessageBase
        reply_chat, reply_msg = self.msg_get_reply_params(update)
        if isinstance(result, (SendableMessageBase, Message, str, list, tuple)):
            return list(self.send_messages(result, reply_chat, reply_msg))
        elif result is False or result is None:
            logger.debug("Ignored result {res!r}".format(res=result))
            # ignore it
        else:
            logger.warning("Unexpected plugin result: {type}".format(type=type(result)))
        # end if
    # end def

    @staticmethod
    def msg_get_reply_params(update):
        """
        Builds the `reply_chat` (chat id) and `reply_msg` (message id) values needed for `Message.send(...)` from an telegram `pytgbot` `Update` instance.

        :param update: pytgbot.api_types.receivable.updates.Update
        :return: reply_chat, reply_msg
        :rtype: tuple(int,int)
        """
        assert_type_or_raise(update, Update, parameter_name="update")
        assert isinstance(update, Update)

        if update.message and update.message.chat.id and update.message.message_id:
            return update.message.chat.id, update.message.message_id
        # end if
        if update.channel_post and update.channel_post.chat.id and update.channel_post.message_id:
            return update.channel_post.chat.id, update.channel_post.message_id
        # end if
        if update.edited_message and update.edited_message.chat.id and update.edited_message.message_id:
            return update.edited_message.chat.id, update.edited_message.message_id
        # end if
        if update.edited_channel_post and update.edited_channel_post.chat.id and update.edited_channel_post.message_id:
            return update.edited_channel_post.chat.id, update.edited_channel_post.message_id
        # end if
        if update.callback_query and update.callback_query.message:
            message_id = update.callback_query.message.message_id if update.callback_query.message.message_id else None
            if update.callback_query.message.chat and update.callback_query.message.chat.id:
                return update.callback_query.message.chat.id, message_id
            # end if
            if update.callback_query.message.from_peer and update.callback_query.message.from_peer.id:
                return update.callback_query.message.from_peer.id, message_id
            # end if
        # end if
        if update.inline_query and update.inline_query.from_peer and update.inline_query.from_peer.id:
            return update.inline_query.from_peer.id, None
        # end if
        return None, None
    # end def

    def send_messages(self, messages, reply_chat, reply_msg):
        """
        Sends a Message.
        Plain strings will become an unformatted TextMessage.
        Supports to mass send lists, tuples, Iterable.

        :param messages: A Message object.
        :type  messages: Message | str | list | tuple |
        :param reply_chat: chat id
        :type  reply_chat: int
        :param reply_msg: message id
        :type  reply_msg: int
        :param instant: Send without waiting for the plugin's function to be done. True to send as soon as possible.
        False or None to wait until the plugin's function is done and has returned, messages the answers in a bulk.
        :type  instant: bool or None
        """
        from pytgbot.exceptions import TgApiException
        from ..messages import Message, TextMessage
        from ..new_messages import SendableMessageBase

        logger.debug("Got {}".format(messages))
        if not isinstance(messages, (SendableMessageBase, Message, str, list, tuple)):
            raise TypeError("Is not a Message type (or str or tuple/list).")
        # end if
        if isinstance(messages, tuple):
            messages = [x for x in messages]
        # end if
        if not isinstance(messages, list):
            messages = [messages]
        # end if
        assert isinstance(messages, list)
        for msg in messages:
            if isinstance(msg, str):
                assert not isinstance(messages, str)  # because we would split a string to pieces.
                msg = TextMessage(msg, parse_mode="text")
            # end if
            if not isinstance(msg, (Message, SendableMessageBase)):
                raise TypeError("Is not a Message/SendableMessageBase type.")
            # end if
            # if msg._next_msg:  # TODO: Reply message?
            #     message.insert(message.index(msg) + 1, msg._next_msg)
            #     msg._next_msg = None
            from requests.exceptions import RequestException
            msg._apply_update_receiver(receiver=reply_chat, reply_id=reply_msg)
            try:
                yield msg.send(self.bot)
            except (TgApiException, RequestException):
                logger.exception("Manager failed messages. Message was {msg!s}".format(msg=msg))
            # end try
        # end for
    # end def

    def send_message(self, messages, reply_chat, reply_msg):
        """
        Backwards compatible version of send_messages.

        :param messages:
        :param reply_chat: chat id
        :type  reply_chat: int
        :param reply_msg: message id
        :type  reply_msg: int
        :return: None
        """
        list(self.send_messages(messages, reply_chat=reply_chat, reply_msg=reply_msg))
        return None
    # end def

    @property
    def bot(self):
        """
        :return: Returns the bot
        :rtype: Bot
        """
        return self._bot
    # end def

    @property
    def me(self) -> User:
        """
        Returns the info about the registered bot
        :return: info about the registered bot user
        """
        return self._me
    # end def

    @property
    def username(self) -> str:
        """
        Returns the name of the registered bot
        :return: the name
        """
        return self.me.username
    # end def

    @property
    def user_id(self):
        return self.me
    # end def

    @property
    def _api_key(self):
        return self.__api_key
    # end def

    on_update = UpdateFilter.decorator
    on_message = MessageFilter.decorator
    on_command = CommandFilter.decorator

    command = on_command
