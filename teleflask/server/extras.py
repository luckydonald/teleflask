# -*- coding: utf-8 -*-
import abc
import os
from typing import Union, List, Callable, Dict

from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.logger import logging
from pytgbot import Bot
from pytgbot.api_types import TgBotApiObject
from pytgbot.api_types.receivable.peer import User
from pytgbot.api_types.receivable.updates import Update
from pytgbot.exceptions import TgApiServerException

from exceptions import AbortProcessingPlease
from .blueprints import TBlueprint
from .filters import MessageFilter, UpdateFilter, CommandFilter, NoMatch, Filter
from .. import VERSION
from .utilities import _class_self_decorate

__author__ = 'luckydonald'
__all__ = ["Teleflask"]
logger = logging.getLogger(__name__)


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
# end class


_self_jsonify = _class_self_decorate("jsonify")  # calls self.jsonify(...) with the result of the decorated function.


class Teleflask(Teleserver):
    VERSION = VERSION
    __version__ = VERSION

    def __init__(
        self, api_key, app=None, blueprint=None, hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
        debug_routes=False, disable_setting_webhook_route=None, disable_setting_webhook_telegram=None,
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
        :type  blueprint: flask.Blueprint | None

        :param hostname: The hostname or IP (and maybe a port) where this server is reachable in the internet.
                         Specify the path with `hostpath`
                         Used to calculate the webhook url.
                         Also configurable via environment variables. See calculate_webhook_url()
        :type  hostname: None|str

        :param hostpath: The host url the base of where this bot is reachable.
                         Examples: None (for root of server) or "/bot2"
                         Note: The webhook will only be set on initialisation.
                         Also configurable via environment variables. See calculate_webhook_url()
        :type  hostpath: None|str

        :param hookpath: The endpoint of the telegram webhook.
                        Defaults to "/income/<API_KEY>"
                        Note: The webhook will only be set on initialisation.
                        Also configurable via environment variables. See calculate_webhook_url()
        :type  hookpath: str

        :param debug_routes: Add extra url endpoints usefull for debugging. See setup_routes(...)
        :type  debug_routes: bool

        :param disable_setting_webhook_telegram: Disable updating the telegram webhook when starting.
                                                 Useful for unit tests. Defaults to the app's config
                                                 DISABLE_SETTING_ROUTE_WEBHOOK or False.
        :type  disable_setting_webhook_telegram: None|bool

        :param disable_setting_webhook_route: Disable creation of the webhook route.
                                              Usefull if you don't need to listen for incomming events.
        :type  disable_setting_webhook_route: None|bool

        :param return_python_objects: Enable return_python_objects in pytgbot. See pytgbot.bot.Bot
        """
        super().__init__(api_key, app, blueprint, hostname, hostpath, hookpath, debug_routes,
                         disable_setting_webhook_telegram, disable_setting_webhook_route, return_python_objects)
        self.app = None  # will be filled out by self.init_app(...)
        self.blueprint = None  # will be filled out by self.init_app(...)
        self.__webhook_url = None  # will be filled out by self.calculate_webhook_url() in self.init_app(...)
        self.hostname = hostname  # e.g. "example.com:443"
        self.hostpath = hostpath
        self.hookpath = hookpath

        if disable_setting_webhook_route is None:
            try:
                self.disable_setting_webhook_route = self.app.config["DISABLE_SETTING_WEBHOOK_ROUTE"]
            except (AttributeError, KeyError):
                logger.debug(
                    'disable_setting_webhook_route is None and app is None or app has no DISABLE_SETTING_WEBHOOK_ROUTE'
                    ' config. Assuming False.'
                )
                self.disable_setting_webhook_route = False
            # end try
        else:
            self.disable_setting_webhook_route = disable_setting_webhook_route
        # end if

        if disable_setting_webhook_telegram is None:
            try:
                self.disable_setting_webhook_telegram = self.app.config["DISABLE_SETTING_WEBHOOK_TELEGRAM"]
            except (AttributeError, KeyError):
                logger.debug(
                    'disable_setting_webhook_telegram is None and app is None or app has no DISABLE_SETTING_WEBHOOK_TELEGRAM'
                    ' config. Assuming False.'
                )
                self.disable_setting_webhook_telegram = False
            # end try
        else:
            self.disable_setting_webhook_telegram = disable_setting_webhook_telegram
        # end if

        if app or blueprint:  # if we have an app or flask blueprint call init_app for adding the routes, which calls init_bot as well.
            self.init_app(app, blueprint=blueprint, debug_routes=debug_routes)
        elif api_key:  # otherwise if we have at least an api key, call init_bot.
            self.init_bot()
        # end if

        self.update_listener = list()
        self.commands = dict()
    # end def

    def init_bot(self):
        """
        Creates the bot, and retrieves information about the bot itself (username, user_id) from telegram.

        :return:
        """
        if not self._bot:  # so you can manually set it before calling `init_app(...)`,
            # e.g. a mocking bot class for unit tests
            self._bot = Bot(self._api_key, return_python_objects=self._return_python_objects)
        elif self._bot.return_python_objects != self._return_python_objects:
            # we don't have the same setting as the given one
            raise ValueError("The already set bot has return_python_objects {given}, but we have {our}".format(
                given=self._bot.return_python_objects, our=self._return_python_objects
            ))
        # end def
        myself = self._bot.get_me()
        if self._bot.return_python_objects:
            self._me = myself
        else:
            assert isinstance(myself, dict)
            self._me = User.from_array(myself["result"])
        # end if
    # end def

    def init_app(self, app, blueprint=None, debug_routes=False):
        """
        Gives us access to the flask app (and optionally provide a Blueprint),
        where we will add a routing endpoint for the telegram webhook.

        Calls `self.init_bot()`, calculates and sets webhook routes, and finally runs `self.do_startup()`.

        :param app: the :class:`flask.Flask` app
        :type  app: flask.Flask

        :param blueprint: A blueprint, where the telegram webhook (and the debug endpoints, see `debug_routes`) will be registered in.
                          If `None` was provided, it will register any routes to the `app` itself.
                          Note: this is NOT a `TBlueprint`, but a regular `flask` one!
        :type  blueprint: flask.Blueprint | None

        :param debug_routes: Add extra url endpoints, useful for debugging. See setup_routes(...)
        :type  debug_routes: bool

        :return: None
        :rtype: None
        """
        self.app = app
        self.blueprint = blueprint
        self.init_bot()
        hookpath, self.__webhook_url = self.calculate_webhook_url(hostname=self.hostname, hostpath=self.hostpath, hookpath=self.hookpath)
        self.setup_routes(hookpath=hookpath, debug_routes=debug_routes)
        self.set_webhook_telegram()  # this will set the webhook in the bot api.
        self.do_startup()  # this calls the startup listeners of extending classes.
    # end def

    def calculate_webhook_url(self, hostname=None, hostpath=None, hookpath="/income/{API_KEY}"):
        """
        Calculates the webhook url.
        Please note, this doesn't change any registered view function!
        Returns a tuple of the hook path (the url endpoint for your flask app) and the full webhook url (for telegram)
        Note: Both can include the full API key, as replacement for ``{API_KEY}`` in the hookpath.

        :Example:

        Your bot is at ``https://example.com:443/bot2/``,
        you want your flask to get the updates at ``/tg-webhook/{API_KEY}``.
        This means Telegram will have to send the updates to ``https://example.com:443/bot2/tg-webhook/{API_KEY}``.

        You now would set
            hostname = "example.com:443",
            hostpath = "/bot2",
            hookpath = "/tg-webhook/{API_KEY}"

        Note: Set ``hostpath`` if you are behind a reverse proxy, and/or your flask app root is *not* at the web server root.


        :param hostname: A hostname. Without the protocol.
                         Examples: "localhost", "example.com", "example.com:443"
                         If None (default), the hostname comes from the URL_HOSTNAME environment variable, or from http://ipinfo.io if that fails.
        :param hostpath: The path after the hostname. It must start with a slash.
                         Use this if you aren't at the root at the server, i.e. use url_rewrite.
                         Example: "/bot2"
                         If None (default), the path will be read from the URL_PATH environment variable, or "" if that fails.
        :param hookpath: Template for the route of incoming telegram webhook events. Must start with a slash.
                         The placeholder {API_KEY} will replaced with the telegram api key.
                         Note: This doesn't change any routing. You need to update any registered @app.route manually!
        :return: the tuple of calculated (hookpath, webhook_url).
        :rtype: tuple
        """
        import os, requests
        # #
        # #  try to fill out empty arguments
        # #
        if not hostname:
            hostname = os.getenv('URL_HOSTNAME', None)
        # end if
        if hostpath is None:
            hostpath = os.getenv('URL_PATH', "")
        # end if
        if not hookpath:
            hookpath = "/income/{API_KEY}"
        # end if
        # #
        # #  check if the path looks at least a bit valid
        # #
        logger.debug("hostname={hostn!r}, hostpath={hostp!r}, hookpath={hookp!r}".format(
            hostn=hostname, hostp=hostpath, hookp=hookpath
        ))
        if hostname:
            if hostname.endswith("/"):
                raise ValueError("hostname can't end with a slash: {value}".format(value=hostname))
            # end if
            if hostname.startswith("https://"):
                hostname = hostname[len("https://"):]
                logger.warning("Automatically removed \"https://\" from hostname. Don't include it.")
            # end if
            if hostname.startswith("http://"):
                raise ValueError("Don't include the protocol ('http://') in the hostname. "
                                 "Also telegram doesn't support http, only https.")
            # end if
        else:  # no hostname
            info = requests.get('http://ipinfo.io').json()
            hostname = str(info["ip"])
            logger.warning("URL_HOSTNAME env not set, falling back to ip address: {ip!r}".format(ip=hostname))
        # end if
        if not hostpath == "" and not hostpath.startswith("/"):
            logger.info("hostpath didn't start with a slash: {value!r} Will be added automatically".format(value=hostpath))
            hostpath = "/" + hostpath
        # end def
        if not hookpath.startswith("/"):
            raise ValueError("hookpath must start with a slash: {value!r}".format(value=hostpath))
        # end def
        hookpath = hookpath.format(API_KEY=self._api_key)
        if not hostpath:
            logger.info("URL_PATH is not set.")
        webhook_url = "https://{hostname}{hostpath}{hookpath}".format(hostname=hostname, hostpath=hostpath, hookpath=hookpath)
        logger.debug("host={hostn!r}, hostpath={hostp!r}, hookpath={hookp!r}, hookurl={url!r}".format(
            hostn=hostname, hostp=hostpath, hookp=hookpath, url=webhook_url
        ))
        return hookpath, webhook_url
    # end def

    def set_webhook_telegram(self):
        """
        Sets the telegram webhook.
        Checks Telegram if there is a webhook set, and if it needs to be changed.

        :return:
        """
        assert isinstance(self.bot, Bot)
        existing_webhook = self.bot.get_webhook_info()

        if self._return_python_objects:
            from pytgbot.api_types.receivable import WebhookInfo
            assert isinstance(existing_webhook, WebhookInfo)
            webhook_url = existing_webhook.url
            webhook_meta = existing_webhook.to_array()
        else:
            assert isinstance(existing_webhook, dict)
            webhook_url = existing_webhook["result"]["url"]
            webhook_meta = existing_webhook["result"]
        # end def
        del existing_webhook
        logger.info("Last webhook pointed to {url!r}.\nMetadata: {hook}".format(
            url=self.hide_api_key(webhook_url), hook=self.hide_api_key("{!r}".format(webhook_meta))
            ))
        if webhook_url == self._webhook_url:
            logger.info("Webhook set correctly. No need to change.")
        else:
            if not self.disable_setting_webhook_telegram:
                logger.info("Setting webhook to {url}".format(url=self.hide_api_key(self._webhook_url)))
                logger.debug(self.bot.set_webhook(url=self._webhook_url))
            else:
                logger.info(
                    "Would set webhook to {url!r}, but action is disabled by DISABLE_SETTING_TELEGRAM_WEBHOOK config "
                    "or disable_setting_webhook_telegram argument.".format(url=self.hide_api_key(self._webhook_url))
                )
            # end if
        # end if
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
    # end def

    def hide_api_key(self, string):
        """
        Replaces the api key with "<API_KEY>" in a given string.

        Note: if the given object is no string, :meth:`str(object)` is called first.

        :param string: The str which can contain the api key.
        :return: string with the key replaced
        """
        if not isinstance(string, str):
            string = str(string)
        # end if
        return string.replace(self._api_key, "<API_KEY>")
    # end def

    def jsonify(self, func):
        """
        Decorator.
        Converts the returned value of the function to json, and sets mimetype to "text/json".
        It will also automatically replace the api key where found in the output with "<API_KEY>".

        Usage:
            @app.route("/foobar")
            @app.jsonify
            def foobar():
               return {"foo": "bar"}
            # end def
            # app is a instance of this class


        There are some special cases to note:

        - :class:`tuple` is interpreted as (data, status).
            E.g.
                return {"error": "not found"}, 404
            would result in a 404 page, with json content {"error": "not found"}

        - :class:`flask.Response` will be returned directly, except it is in a :class:`tuple`
            In that case the status code of the returned response will be overwritten by the second tuple element.

        - :class:`TgBotApiObject` will be converted to json too. Status code 200.

        - An exception will be returned as `{"error": "exception raised"}` with status code 503.


        :param func: the function to wrap
        :return: the wrapped function returning json responses.
        """
        from functools import wraps
        from flask import Response
        import json
        logger.debug("func: {}".format(func))

        @wraps(func)
        def jsonify_inner(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except:
                logger.exception("failed executing {name}.".format(name=func.__name__), exc_info=True)
                result = {"error": "exception raised"}, 503
            # end def
            status = None  # will be 200 if not otherwise changed
            if isinstance(result, tuple):
                response, status = result
            else:
                response = result
            # end if
            if isinstance(response, Response):
                if status:
                    response.status_code = status
                # end if
                return response
            # end if
            if isinstance(response, TgBotApiObject):
                response = response.to_array()
            # end if
            response = json.dumps(response)
            # end if
            assert isinstance(response, str)
            response_kwargs = {}
            response_kwargs.setdefault("mimetype", "text/json")
            if status:
                response_kwargs["status"] = status
            # end if
            res = Response(self.hide_api_key(response), **response_kwargs)
            logger.debug("returning: {}".format(res))
            return res
        # end def inner
        return jsonify_inner
    # end def

    @_self_jsonify
    def view_exec(self, api_key, command):
        """
        Issue commands. E.g. /exec/TELEGRAM_API_KEY/getMe

        :param api_key: gets checked, so you can't just execute commands.
        :param command: the actual command
        :return:
        """
        if api_key != self._api_key:
            error_msg = "Wrong API key: {wrong_key!r}".format(wrong_key=api_key)
            logger.warning(error_msg)
            return {"status": "error", "message": error_msg, "error_code": 403}, 403
        # end if
        from flask import request
        from pytgbot.exceptions import TgApiServerException
        logger.debug("COMMAND: {cmd}, ARGS: {args}".format(cmd=command, args=request.args))
        try:
            res = self.bot.do(command, **request.args)
            if self._return_python_objects:
                return res.to_array()
            else:
                return res
            # end if
        except TgApiServerException as e:
            return {"status": "error", "message": e.description, "error_code": e.error_code}, e.error_code
        # end try
    # end def

    @_self_jsonify
    def view_status(self):
        """
        Returns the status about the bot's webhook.

        :return: webhook info
        """
        try:
            res = self.bot.get_webhook_info()  # TODO: fix to work with return_python_objects==False
            return res.to_array()
        except TgApiServerException as e:
            return {"status": "error", "message": e.description, "error_code": e.error_code}, e.error_code
        # end try

    @_self_jsonify
    def view_updates(self):
        """
        This processes incoming telegram updates.

        :return:
        """
        from pprint import pformat
        from flask import request

        logger.debug("INCOME:\n{}\n\nHEADER:\n{}".format(
            pformat(request.get_json()),
            request.headers if hasattr(request, "headers") else None
        ))
        update = Update.from_array(request.get_json())
        try:
            result = self.process_update(update)
        except Exception as e:
            logger.exception("process_update()")
            result = {"status": "error", "message": str(e)}
        result = result if result else {"status": "probably ok"}
        logger.info("returning result: {}".format(result))
        return result
    # end def

    @_self_jsonify
    def view_host_info(self):
        """
        Get infos about your host, like IP etc.
        :return:
        """
        import socket
        import requests
        info = requests.get('http://ipinfo.io').json()
        info["host"] = socket.gethostname()
        info["version"] = self.VERSION
        return info
    # end def

    @_self_jsonify
    def view_routes_info(self):
        """
        Get infos about your host, like IP etc.
        :return:
        """
        from werkzeug.routing import Rule
        routes = []
        for rule in self.app.url_map.iter_rules():
            assert isinstance(rule, Rule)
            routes.append({
                'methods': list(rule.methods),
                'rule': rule.rule,
                'endpoint': rule.endpoint,
                'subdomain': rule.subdomain,
                'redirect_to': rule.redirect_to,
                'alias': rule.alias,
                'host': rule.host,
                'build_only': rule.build_only
            })
        # end for
        return routes
    # end def

    @_self_jsonify
    def view_request(self):
        """
        Get infos about your host, like IP etc.
        :return:
        """
        import json
        from flask import session
        j = json.loads(json.dumps(session)),
        # end for
        return j
    # end def

    def get_router(self):
        """
        Where to call `add_url_rule` (aka. `@route`) on.
        Returns either the blueprint if there is any, or the app.

        :raises ValueError: if neither blueprint nor app is set.

        :returns: either the blueprint if it is set, or the app.
        :rtype: flask.Blueprint | flask.Flask
        """
        if self.blueprint:
            return self.blueprint
        # end if
        if not self.app:
            raise ValueError("The app (self.app) is not set.")
        # end if
        return self.app

    def setup_routes(self, hookpath, debug_routes=False):
        """
        Sets the pathes to the registered blueprint/app:
            - "webhook"  (self.view_updates) at hookpath
        Also, if `debug_routes` is `True`:
            - "exec"     (self.view_exec)        at "/teleflask_debug/exec/API_KEY/<command>"  (`API_KEY` is replaced, `<command>` is any Telegram API command.)
            - "status"   (self.view_status)      at "/teleflask_debug/status"
            - "hostinfo" (self.view_host_info)   at "/teleflask_debug/hostinfo"
            - "routes"   (self.view_routes_info) at "/teleflask_debug/routes"

        :param hookpath: The path where it expects telegram updates to hit the flask app/blueprint.
        :type  hookpath: str

        :param debug_routes: Add several debug paths.
        :type  debug_routes: bool
        """
        # Todo: Find out how to handle blueprints
        if not self.app and not self.blueprint:
            raise ValueError("No app (self.app) or Blueprint (self.blueprint) was set.")
        # end if
        router = self.get_router()
        if not self.disable_setting_webhook_route:
            logger.info("Adding webhook route: {url!r}".format(url=hookpath))
            assert hookpath
            router.add_url_rule(hookpath, endpoint="webhook", view_func=self.view_updates, methods=['POST'])
        else:
            logger.info("Not adding webhook route, because disable_setting_webhook=True")
        # end if
        if debug_routes:
            logger.info("Adding debug routes.".format(url=hookpath))
            router.add_url_rule("/teleflask_debug/exec/{api_key}/<command>".format(api_key=self._api_key), endpoint="exec", view_func=self.view_exec)
            router.add_url_rule("/teleflask_debug/status", endpoint="status", view_func=self.view_status)
            router.add_url_rule("/teleflask_debug/routes", endpoint="routes", view_func=self.view_routes_info)
        # end if
    # end def

    @property
    def _webhook_url(self):
        return self.__webhook_url
    # end def
# end class


class PollingTeleflask(Teleflask):
    def __init__(self, api_key, app=None, blueprint=None, hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
                 debug_routes=False, disable_setting_webhook=True, return_python_objects=True, https=True, start_process=True):
        # https: if we should use https for our host.
        # start_process: If the proxy process should be started.
        if not disable_setting_webhook:
            logger.warn(
                'You are using the {clazz} class to use poll based updates for debugging, but requested creating a '
                'webhook route (disable_setting_webhook is set to False).'.format(
                clazz=self.__class__.__name__
            ))
        # end if
        self.https = https
        self.start_process = start_process
        super().__init__(api_key, app, blueprint, hostname, hostpath, hookpath, debug_routes, disable_setting_webhook,
                         return_python_objects)

    def calculate_webhook_url(self, hostname=None, hostpath=None, hookpath="/income/{API_KEY}"):
        return super().calculate_webhook_url(hostname if hostname else os.getenv('URL_HOSTNAME', 'localhost'), hostpath, hookpath)
    # end def

    def set_webhook_telegram(self):
        """
        We need to unset a telegram webhook if any.
        """
        pass
    # end def

    def do_startup(self):
        """
        Uses the get updates method to run.
        Checks Telegram if there is a webhook set, and if it needs to be changed.

        :return:
        """
        super().do_startup()
        if self.start_process:
            self._start_proxy_process()
        # end def
    # end def

    def _start_proxy_process(self):
        from ..proxy import proxy_telegram
        from multiprocessing import Process
        global telegram_proxy_process
        telegram_proxy_process = Process(target=proxy_telegram, args=(), kwargs=dict(
            api_key=self._api_key, https=self.https, host=self.hostname, hookpath=self.hookpath
        ))
        telegram_proxy_process.start()
    # end def
# end class

