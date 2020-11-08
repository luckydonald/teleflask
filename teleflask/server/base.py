# -*- coding: utf-8 -*-
import abc

from pytgbot import Bot
from pytgbot.api_types import TgBotApiObject
from pytgbot.exceptions import TgApiServerException
from pytgbot.api_types.receivable.updates import Update as TGUpdate
from luckydonaldUtils.logger import logging
from luckydonaldUtils.exceptions import assert_type_or_raise

from .. import VERSION
from .utilities import _class_self_decorate

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

_self_jsonify = _class_self_decorate("jsonify")  # calls self.jsonify(...) with the result of the decorated function.


class TeleflaskMixinBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def process_update(self, update):
        """
        This method is called from the flask webserver.

        Any Mixin implementing must call super().process_update(update).
        So catch exceptions in your mixin's code.

        :param update: The Telegram update
        :type  update: pytgbot.api_types.receivable.updates.Update
        :return:
        """
        return
    # end def

    @abc.abstractmethod
    def do_startup(self):
        """
        This method is called on bot/server startup.
        To be precise, `TeleflaskBase.init_app()` will call it when done.

        Any Mixin implementing **must** call `super().do_startup(update)`.
        So catch any and all exceptions in your mixin's own code.
        :return:
        """
        return
    # end def
# end class


class TeleflaskBase(TeleflaskMixinBase):
    VERSION = VERSION
    __version__ = VERSION

    def __init__(self, api_key, app=None, blueprint=None,
                 # FlaskTgBot kwargs:
                 hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
                 debug_routes=False, disable_setting_webhook_route=None, disable_setting_webhook_telegram=None,
                 # pytgbot kwargs:
                 return_python_objects=True):
        """
        A new Teleflask(Base) object.

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
        self.__api_key = api_key
        self._bot = None  # will be set in self.init_bot()
        self.app = None  # will be filled out by self.init_app(...)
        self.blueprint = None  # will be filled out by self.init_app(...)
        self._return_python_objects = return_python_objects
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
            self._user_id = myself.id
            self._username = myself.username
        else:
            self._user_id = myself["result"]["id"]
            self._username = myself["result"]["username"]
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

    @property
    def bot(self):
        """
        :return: Returns the bot
        :rtype: Bot
        """
        return self._bot
    # end def
    @property
    def username(self):
        """
        Returns the name of the registerd bot
        :return:
        """
        return self._username
    # end def

    @property
    def user_id(self):
        return self._user_id
    # end def

    @property
    def _webhook_url(self):
        return self.__webhook_url
    # end def

    @property
    def _api_key(self):
        return self.__api_key
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
        This code is executed after server boot.

        Sets the telegram webhook (see :meth:`set_webhook_telegram(self)`)
        and calls `super().do_setup()` for the superclass (e.g. other mixins)

        :return:
        """
        super().do_startup()  # do more registered startup actions.
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
        update = TGUpdate.from_array(request.get_json())
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

    @abc.abstractmethod
    def process_update(self, update):
        return
    # end def

    def process_result(self, update, result):
        """
        Send the result.
        It may be a :class:`Message` or a list of :class:`Message`s
        Strings will be send as :class:`TextMessage`, encoded as raw text.

        :param update: A telegram incoming update
        :type  update: TGUpdate

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
        assert_type_or_raise(update, TGUpdate, parameter_name="update")
        assert isinstance(update, TGUpdate)

        if update.message and update.message.migrate_to_chat_id:
            return update.message.migrate_to_chat_id, update.message.message_id
        # end if
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
# end class
