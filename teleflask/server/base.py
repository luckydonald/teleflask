# -*- coding: utf-8 -*-
import abc

from pytgbot import Bot
from pytgbot.api_types import TgBotApiObject
from pytgbot.exceptions import TgApiServerException
from luckydonaldUtils.logger import logging

from .. import VERSION
from .utilities import _class_self_decorate

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

_self_jsonify = _class_self_decorate("jsonify")


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

        Any Mixin implementing must call super().do_startup(update).
        So catch exceptions in your mixin's code.
        :return:
        """
        return
    # end def
# end class


class TeleflaskBase(TeleflaskMixinBase):
    VERSION = VERSION
    __version__ = VERSION

    def __init__(self, api_key, app=None,
                 # FlaskTgBot kwargs:
                 hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
                 debug_routes=False, disable_setting_webhook=False,
                 # pytgbot kwargs:
                 return_python_objects=True):
        """

        :param api_key: The key for the telegram bot api.
        :type  api_key: str

        :param app: The flask app

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

        :param disable_setting_webhook: Disable updating the webhook when starting. Useful for unit tests.

        :param return_python_objects: Enable return_python_objects in pytgbot. See pytgbot.bot.Bot
        """
        self.__api_key = api_key
        self.update_listener = list()
        self.commands = dict()
        self._return_python_objects = return_python_objects
        self.bot = Bot(api_key, return_python_objects=return_python_objects)
        myself = self.bot.get_me()
        if self._return_python_objects:
            self._user_id = myself.id
            self._username = myself.username
        else:
            self._user_id = myself["result"]["id"]
            self._username = myself["result"]["username"]
        # end if
        self._webhook_url = None  # will be filled out by self.calculate_webhook_url() in self.init_app(...)
        self.hostname = hostname  # e.g. "example.com:443"
        self.hostpath = hostpath
        self.hookpath = hookpath
        self.disable_setting_webhook=disable_setting_webhook
        if app:
            self.init_app(app, debug_routes=debug_routes)
        # end if
    # end def

    def init_app(self, app, debug_routes=False):
        """
        Sets the flask app, the telegram webhook and adds a routing endpoint.
        Finally calls `self.do_startup()`

        :param app: the :class:`flask.Flask` app
        :type  app: flask.Flask

        :param debug_routes: Add extra url endpoints, useful for debugging. See setup_routes(...)
        :type  debug_routes: bool

        :return: None
        :rtype: None
        """
        self.app = app
        hookpath, self._webhook_url = self.calculate_webhook_url(hostname=self.hostname, hostpath=self.hostpath, hookpath=self.hookpath)
        self.setup_routes(hookpath=hookpath, debug_routes=debug_routes)
        self.do_startup()  # this will set the webhook in the bot api.

    def calculate_webhook_url(self, hostname=None, hostpath=None, hookpath="/income/{API_KEY}"):
        """
        Calculates the webhook url.
        Please note, this doesn't change any registered view function!
        Returns a tuple of the hook path (the url endpoint for your flask app) and the full webhook url (for telegram)
        Note: Both can include the full API key, as replacement for ``{API_KEY}`` in the hookpath.

        :Example:

        Your bot is at ``https://example.com:443/bot2/``,
        and you want to receive updates from telegram at ``https://example.com:443/bot2/tg-webhook/{API_KEY}``.
        You now would set
            hostname = "example.com:443",
            hostpath = "/bot2",
            hookpath = "/tg-webhook/{API_KEY}"

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
        logger.debug("hostname={hostn}, hostpath={hostp}, hookpath={hookp}".format(
            hostn=hostname, hostp=hostpath, hookp=hookpath
        ))
        if hostname.endswith("/"):
            raise ValueError("hostname can't end with a slash: {value}".format(value=hostname))
        if hostname.startswith("https://"):
            hostname = hostname[len("https://"):]
            logger.warning("Automatically removed \"https://\" from hostname. Don't include it.")
        if hostname.startswith("http://"):
            raise ValueError("Don't include the protocol ('http://') in the hostname. "
                             "Also telegram doesn't support http, only https.")
        if not hostpath == "" and not hostpath.startswith("/"):
            logger.info("hostpath didn't start with a slash: {value!r} Will be added automatically".format(value=hostpath))
            hostpath = "/" + hostpath
        # end def
        if not hookpath.startswith("/"):
            raise ValueError("hookpath must start with a slash: {value!r}".format(value=hostpath))
        # end def
        hookpath = hookpath.format(API_KEY=self.__api_key)
        if not hostname:
            info = requests.get('http://ipinfo.io').json()
            hostname = str(info["ip"])
            logger.warning("URL_HOSTNAME env not set, falling back to ip address: {ip!r}".format(ip=hostname))
        # end if
        if not hostpath:
            logger.info("URL_PATH is not set.")
        webhook_url = "https://{hostname}{hostpath}{hookpath}".format(hostname=hostname, hostpath=hostpath, hookpath=hookpath)
        return hookpath, webhook_url
    # end def

    @property
    def username(self):
        return self._username
    # end def

    @property
    def user_id(self):
        return self._user_id
    # end def

    @property
    def webhook_url(self):
        return self._webhook_url
    # end def

    def do_startup(self):
        """
        This code is executed after server boot.
        Sets the telegram webhook.

        :return:
        """
        assert isinstance(self.bot, Bot)
        webhook = self.bot.get_webhook_info()

        if self._return_python_objects:
            from pytgbot.api_types.receivable import WebhookInfo
            assert isinstance(webhook, WebhookInfo)
            webhook_url = webhook.url
            webhook_meta = webhook.to_array()
        else:
            webhook_url = webhook["result"]["url"]
            webhook_meta = webhook["result"]
        # end def
        del webhook
        logger.info("Last webhook pointed to {url!r}.\nMetadata: {hook}".format(
            url=self.hide_api_key(webhook_url), hook=self.hide_api_key("{!r}".format(webhook_meta))
            ))
        if webhook_url == self.webhook_url:
            logger.info("Webhook set correctly. No need to change.")
        else:
            if not self.app.config.get("DISABLE_SETTING_TELEGRAM_WEBHOOK", False):
                logger.info("Setting webhook to {url}".format(url=self.hide_api_key(self.webhook_url)))
                logger.debug(self.bot.set_webhook(url=self.webhook_url))
            else:
                logger.info("Would set webhook to {url!r}, but is disabled by DISABLE_SETTING_TELEGRAM_WEBHOOK config.".format(url=self.hide_api_key(self.webhook_url)))
            # end if
        # end if
        super().do_startup()
    # end def

    def hide_api_key(self, string):
        """
        Replaces the api key with "<API_KEY>"

        :param string: The str which can contain the api key.
        :return: string with the key replaced
        """
        if not string:
            return ""
        # end if
        return string.replace(self.__api_key, "<API_KEY>")
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
        if api_key != self.__api_key:
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
        from pytgbot.api_types.receivable.updates import Update

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
    def view_hostinfo(self):
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

    def setup_routes(self, hookpath, debug_routes=False):
        """
        Sets the
        :param hookpath: The path where it expects telegram updates to hit flask.
        :param debug_paths: Add paths to enable several debug stuff.
        :return:
        """
        # Todo: Find out how to handle blueprints
        if not self.app:
            raise ValueError("The app (self.app) is not set.")
        # end if
        self.app.add_url_rule(hookpath, endpoint=None, view_func=self.view_updates, methods=['POST'])
        if debug_routes:
            self.app.add_url_rule("/exec/<api_key>/<command>", endpoint=None, view_func=self.view_exec)
            self.app.add_url_rule("/status", endpoint=None, view_func=self.view_status)
            self.app.add_url_rule("/hostinfo", endpoint=None, view_func=self.view_hostinfo)
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

        :param manager:
        :param result:
        :return:
        """
        from ..messages import Message
        reply_to, reply_id = None, None
        if update.message and update.message.chat.id and update.message.message_id:
            reply_to, reply_id = update.message.chat.id, update.message.message_id
        # end if
        if isinstance(result, (Message, str, list, tuple)):
            self.send_message(result, reply_to, reply_id)
        elif result == False or result is None:
            logger.debug("Ignored result {res!r}".format(res=result))
            # ignore it
        else:
            logger.warn("Unexpected plugin result: {type}".format(type=type(result)))
        # end if
    # end def

    def send_message(self, message, reply_to, reply_id):
        """
        Sends a Message.
        Plain strings will become an unformatted TextMessage.
        Supports to mass send lists, tuples, Iterable.

        :param message: A Message object.
        :type  message: Message | str | list | tuple |
        :param instant: Send without waiting for the plugin's function to be done. True to send as soon as possible.
        False or None to wait until the plugin's function is done and has returned, messages the answers in a bulk.
        :type  instant: bool or None
        """
        from pytgbot.exceptions import TgApiException
        from ..messages import Message, TextMessage

        logger.debug("Got {}".format(message))
        if not isinstance(message, (Message, str, list, tuple)):
            raise TypeError("Is not a Message type (or str or tuple/list).")
        # end if
        if isinstance(message, tuple):
            message = [x for x in message]
        # end if
        if not isinstance(message, list):
            message = [message]
        # end if
        assert isinstance(message, list)
        for msg in message:
            if isinstance(msg, str):
                assert not isinstance(message, str)  # because we would split a string to pieces.
                msg = TextMessage(msg, parse_mode="text")
            # end if
            if not isinstance(msg, Message):
                raise TypeError("Is not a Message type.")
            # end if
            # if msg._next_msg:  # TODO: Reply message?
            #     message.insert(message.index(msg) + 1, msg._next_msg)
            #     msg._next_msg = None
            from requests.exceptions import RequestException
            try:
                msg.send(self.bot, reply_to, reply_id)
            except (TgApiException, RequestException):
                logger.exception("Manager failed messages. Message was {msg!s}".format(msg=msg))
            # end try
        # end for
    # end def
# end class
