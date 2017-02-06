# -*- coding: utf-8 -*-
import abc

from flask import Flask
from pytgbot import Bot
from pytgbot.api_types import TgBotApiObject
from pytgbot.exceptions import TgApiServerException
from luckydonaldUtils.logger import logging

from .utilities import _class_self_decorate

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

_class_jsonify = _class_self_decorate("jsonify")


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


class TeleflaskBase(Flask, TeleflaskMixinBase):
    VERSION = "0.0.0"
    def __init__(self, import_name, API_KEY,
                 # FlaskTgBot kwargs:
                 hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
                 # pytgbot kwargs:
                 return_python_objects=True,
                 # flask kwargs:
                 static_path=None, static_url_path=None,
                 static_folder='static', template_folder='templates',
                 instance_path=None, instance_relative_config=False,
                 root_path=None):
        """

        :param import_name: the name of the application package
        :param API_KEY: The key for the telegram bot api.

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

        :param return_python_objects:

        :param static_url_path: can be used to specify a different path for the
                            static files on the web.  Defaults to the name
                            of the `static_folder` folder.
        :param static_folder: the folder with static files that should be served
                              at `static_url_path`.  Defaults to the ``'static'``
                              folder in the root path of the application.
        :param template_folder: the folder that contains the templates that should
                                be used by the application.  Defaults to
                                ``'templates'`` folder in the root path of the
                                application.
        :param instance_path: An alternative instance path for the application.
                              By default the folder ``'instance'`` next to the
                              package or module is assumed to be the instance
                              path.
        :param instance_relative_config: if set to ``True`` relative filenames
                                         for loading the config are assumed to
                                         be relative to the instance path instead
                                         of the application root.
        :param root_path: Flask by default will automatically calculate the path
                          to the root of the application.  In certain situations
                          this cannot be achieved (for instance if the package
                          is a Python 3 namespace package) and needs to be
                          manually defined
        """
        super().__init__(
            import_name,
            static_path=static_path, static_url_path=static_url_path, static_folder=static_folder,
            template_folder=template_folder, instance_path=instance_path,
            instance_relative_config=instance_relative_config, root_path=root_path
        )
        self.__api_key = API_KEY
        self.update_listener = list()
        self.commands = dict()
        self._return_python_objects = return_python_objects
        self.bot = Bot(API_KEY, return_python_objects=return_python_objects)
        myself = self.bot.get_me()
        self._user_id = myself.id  # TODO: fix for return_python_objects == False
        self._username = myself.username  # TODO: fix for return_python_objects == False, like:
        # self._username = self.bot.get_me().result.username  # return_python_objects = False
        self._webhook_url = None  # will be filled out by self.calculate_webhook_url()
        hookpath = self.calculate_webhook_url(hostname=hostname, hostpath=hostpath, hookpath=hookpath)
        self.set_up_default_routes(hookpath=hookpath)
        self.do_startup()
    # end def

    def calculate_webhook_url(self, hostname=None, hostpath=None, hookpath="/income/{API_KEY}"):
        """
        Calculates the webhook url.
        Please note, this doesn't change any registered view function!

        Example:
            Your bot is at "https://example.com:443/bot2/",
            and you want to remove updates from telegram at "https://example.com:443/bot2/tg-webhook/{API_KEY}".
            You now would set
                hostname = "example.com:443",
                hostpath = "/bot2",
                hookpath = "/tg-webhook/{API_KEY}"

        :param hostname: A hostname. Without the protocol.
                         Examples: "localhost", "example.com", "example.com:443"
                         If None (default), the hostname comes from the URL_HOSTNAME environment variable, or None if that fails.
        :param hostpath: The path after the hostname. It must start with a slash.
                         Use this if you aren't at the root at the server, i.e. use url_rewrite.
                         Example: "/bot2"
                         If None (default), the path will be read from the URL_PATH environment variable, or "" if that fails.
        :param hookpath: Template for the route of incoming telegram webhook events. Must start with a slash.
                         The placeholder {API_KEY} will replaced with the telegram api key.
                         Note: This doesn't change any routing. You need to update any registered @app.route manually!
        :return: the calculated hookpath.
        """
        import os, requests
        # #
        # #  try to fill out empty arguments
        # #
        if hostname:
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
            raise ValueError("hookpath must start with a slash: {value}".format(value=hostpath))
        # end def
        hookpath = hookpath.format(API_KEY=self.__api_key)
        if not hostname:
            info = requests.get('http://ipinfo.io').json()
            hostname = str(info["ip"])
            logger.warning("URL_HOSTNAME env not set, falling back to ip address: {ip}".format(ip=hostname))
        # end if
        if not hostpath:
            logger.info("URL_PATH is not set.")
        self._webhook_url = "https://{hostname}{hostpath}{hookpath}".format(hostname=hostname, hostpath=hostpath, hookpath=hookpath)
        return hookpath
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

        :return:
        """
        webhook = self.bot.get_webhook_info()  # todo: dict-version if return_python_objects==False
        from pytgbot.api_types.receivable import WebhookInfo
        assert isinstance(webhook, WebhookInfo)
        logger.info("Last webhook pointed to {url!r}.\nMetadata: {hook}".format(
            url=self.hide_api_key(webhook.url), hook=self.hide_api_key("{!r}".format(webhook.to_array()))
        ))
        if webhook.url == self.webhook_url:
            logger.info("Webhook set correctly. No need to change.")
        else:
            logger.info("Setting webhook to {url}".format(url=self.hide_api_key(self.webhook_url)))
            logger.debug(self.bot.set_webhook(url=self.webhook_url))
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

        - :class:`TgBotApiObject` will be converted to json too.


        :param func: the function to wrap
        :return: the wrapped function returning json responses.
        """
        from functools import wraps
        from flask import Response
        import json
        logger.debug("func: {}".format(func))

        @wraps(func)
        def jsonify_inner(*args, **kwargs):
            result = func(*args, **kwargs)
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

    @_class_jsonify
    def view_exec(self, api_key, command):
        """
        Issue commands. E.g. /exec/TELEGRAM_API_KEY/getMe

        :param command:
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
            res = self.bot.do(command, **request.args)  # TODO: fix to work with return_python_objects==False
            return res.to_array()
        except TgApiServerException as e:
            return {"status": "error", "message": e.description, "error_code": e.error_code}, e.error_code
        # end try
    # end def

    @_class_jsonify
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

    @_class_jsonify
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

    @_class_jsonify
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

    def set_up_default_routes(self, hookpath):
        self.add_url_rule("/exec/<api_key>/<command>", endpoint=None, view_func=self.view_exec)
        self.add_url_rule("/status", endpoint=None, view_func=self.view_status)
        self.add_url_rule("/hostinfo", endpoint=None, view_func=self.view_hostinfo)
        self.add_url_rule(hookpath, endpoint=None, view_func=self.view_updates, methods=['POST'])
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
