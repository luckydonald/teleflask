import json
import requests
import unittest
import os
from unittest import TestLoader
from unittest import mock

import pytgbot
from DictObject import DictObject
from pytgbot import Bot

# from somewhere import API_KEY  # I import it from some file which is kept private, not in git.

import logging
from teleflask import Teleflask
from flask import Flask

logging.basicConfig(level=logging.DEBUG)
API_KEY = "lel1324fakeAPIKEY"


class ResponseTestable(requests.Response):
    def __init__(self, json, status_code, *args, **kwargs):
        self._json = json
        self._status_code = status_code
    # end def

    # not a @property
    def json(self):
        return self._json
    # end def

    @property
    def status_code(self):
        return self._status_code
    # end def

    @property
    def content(self):
        return json.dumps(self._json)
    # end def


class BotTestable(Bot):
    def __init__(self, api_key, return_python_objects=False):
        """
        To enable the result of :meth:`self.do` to return data directly.
            
        :param api_key: Ignored.
        :param return_python_objects: Ignored?
        """
        self.__api_key = "4458:FAKE_API_KEY_FOR_TESTING"
        self.return_python_objects = return_python_objects
        # super().__init__(API_KEY, return_python_objects=False)
    # end def
    fake_responses = DictObject.objectify({
        "getMe": {"ok": True, "result": {
            "id": 1, "first_name": "FAKE BOT FOR TESTING", "username": "BotFather"
        }},
        "getWebhookInfo":{"ok": True, "result": {
            "url": "https://example.com/income/"+API_KEY, "has_custom_certificate": False, "pending_update_count": 0,
            "max_connections": 40
        }},
    })

    def do(self, command, files=None, use_long_polling=False, request_timeout=None, **query):
        """
        Returns the input as dict so that the result of any method is the do arguments.
        :param command:
        :param files:
        :param use_long_polling:
        :param request_timeout:
        :param query:
        :return:
        """
        if command in self.fake_responses:
            r = ResponseTestable(self.fake_responses[command], 200)
            return self._postprocess_request(r)
        # end if
        url, params = self._prepare_request(command, query)

        data = {
            "call": {'command': command, 'files': files, 'use_long_polling': use_long_polling,
                     'request_timeout': request_timeout, '**query': query},
            "url": url,
            "json": params,
            "is_python_object": self.return_python_objects
        }
        return DictObject.objectify(data)
    # end def
# end class


from pytgbot import bot as pytgbot_bot
# replace the Bot in pytgbot with our Mockup, so `isinstance` checks will succeed.
pytgbot.Bot = BotTestable
pytgbot_bot.Bot = BotTestable
# also everywhere where it would be imported.
from teleflask.server import base as tf_s_base
tf_s_base.Bot = BotTestable


class SomeTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("URL_HOSTNAME", "example.com")

        app = Flask(__name__)
        app.config.from_pyfile("testconfig.py")
        self.app = app
        self.app_test = app.test_client()  # get a test client
        self.bot = Teleflask(API_KEY, return_python_objects=True)

        # replace the :class:`pytgbot.Bot` instance with something testable. (not using TG server)
        # All methods now return the stuff they would sent to the telegram servers as json instead.
        # This is not usable with the :class:`teleflask.message.Message` (sub)types.
        self.bot._bot = BotTestable(API_KEY, return_python_objects=self.bot._return_python_objects)
        assert isinstance(self.bot.bot, BotTestable)

        # Init must be before replacing the ``bot.bot``,
        # because else the :meth:`Bot.getWebhook` won't work as expected in startup.
        self.bot.init_app(app)

        # Array to hold information about the called callbacks:
        self.callbacks_status = {}

        # Get the update_path to be able to test via emulating incoming updates
        self.update_path, self.update_url = self.bot.calculate_webhook_url(hostname=self.bot.hostname, hostpath=self.bot.hostpath, hookpath=self.bot.hookpath)

    def tearDown(self):
        pass
        # os.close(self.db_fd)
        # os.unlink(flaskr.app.config['DATABASE'])
    # end def

    data_cmd = {
        "update_id": 10000,
        "message": {
            "message_id": 4458,
            "from": {
                "id": 1234,
                "first_name": "Test User",
                "username": "username",
                "is_bot": False
            },
            "chat": {
                "id": 1234,
                "first_name": "Test User",
                "username": "username",
                "type": "private"
            },
            "date": 1487612335,
            "text": "/test 123",
            "entities": [
                {
                    "type": "bot_command",
                    "offset": 0,
                    "length": 5
                }
            ]
        }
    }

    def test_webhook(self):
        self.assertEqual(self.update_url.replace(API_KEY, "{API_KEY}"), "https://example.com/income/{API_KEY}")
    # end def

    def test_command(self):
        @self.bot.command("test")
        def _callback_test_command(update, text):
            self.callbacks_status["_callback_test_command"] = text
        # end def

        self.app_test.post(self.update_path, data=json.dumps(self.data_cmd), content_type='application/json')

        self.assertIn("_callback_test_command", self.callbacks_status, "@command('test') func executed")
        self.assertEquals(self.callbacks_status["_callback_test_command"], "123")
    # end def

    def test_on_message(self):
        @self.bot.on_message
        def _callback_test_on_message(update, msg):
            self.callbacks_status["_callback_test_on_message"] = msg
        # end def

        self.app_test.post(self.update_path, data=json.dumps(self.data_cmd), content_type='application/json')

        self.assertIn("_callback_test_on_message", self.callbacks_status, "@on_message func executed")
        msg = self.callbacks_status["_callback_test_on_message"]
        from pytgbot.api_types.receivable.updates import Message
        self.assertIsInstance(msg, Message)
        self.assertDictEqual(msg.to_array(), self.data_cmd["message"])
    # end def

    def test_on_message2(self):
        @self.bot.on_message("text")
        def _callback_test_on_message2(update, msg):
            self.callbacks_status["_callback_test_on_message2"] = msg
        # end def

        self.app_test.post(self.update_path, data=json.dumps(self.data_cmd), content_type='application/json')

        self.assertIn("_callback_test_on_message2", self.callbacks_status, "@on_message('text') func executed")
        msg = self.callbacks_status["_callback_test_on_message2"]
        from pytgbot.api_types.receivable.updates import Message
        self.assertIsInstance(msg, Message)
        self.assertDictEqual(msg.to_array(), self.data_cmd["message"])
    # end def

    def test_on_message3(self):
        @self.bot.on_message("photo")
        def _callback_test_on_message3(msg):
            self.callbacks_status["_callback_test_on_message3"] = msg
        # end def

        self.app_test.post(self.update_path, data=json.dumps(self.data_cmd), content_type='application/json')

        self.assertNotIn("_callback_test_on_message3", self.callbacks_status, "@on_message('photo') func not executed")
    # end def
# end class

if __name__ == "__main__":
    unittest.main()
