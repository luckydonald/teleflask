import json
import unittest
import os
from pytgbot import Bot

from somewhere import API_KEY  # I import it from some file which is kept private, not in git.

import logging
from teleflask import Teleflask
from flask import Flask
from teleflask.messages import TextMessage

logging.basicConfig(level=logging.DEBUG)


class BotTestable(Bot):
    def __init__(self, api_key, return_python_objects=True):
        """
        Forces return_python_objects to be False, to enable the result of :meth:`self.do` to return data directly.

        :param api_key:
        :param return_python_objects:
        """
        super().__init__(api_key, return_python_objects=False)
    # end def

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
        url, params = self._prepare_request(command, query)

        data = {
            "call": {'command': command, 'files': files, 'use_long_polling': use_long_polling,
                     'request_timeout': request_timeout, '**query': query},
            "url": url,
            "json": params
        }
        return data
    # end def
# end class


class SomeTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("URL_HOSTNAME", "example.com")

        app = Flask(__name__)
        app.config.from_pyfile("testconfig.py")
        self.app = app
        self.app_test = app.test_client()  # get a test client
        self.bot = Teleflask(API_KEY)

        # Init must be before replacing the ``bot.bot``,
        # because else the :meth:`Bot.getWebhook` won't work as expected in startup.
        self.bot.init_app(app)

        # replace the :class:`pytgbot.Bot` instance with something testable. (not using TG server)
        # All methods now return the stuff they would sent to the telegram servers as json instead.
        # This is not usable with the :class:`teleflask.message.Message` (sub)types.
        self.bot.bot = BotTestable(API_KEY)

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
                "username": "username"
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
        def _callback_test_on_message(msg):
            self.callbacks_status["_callback_test_on_message"] = msg
        # end def

        self.app_test.post(self.update_path, data=json.dumps(self.data_cmd), content_type='application/json')

        self.assertIn("_callback_test_on_message", self.callbacks_status, "@on_message func executed")
        msg = self.callbacks_status["_callback_test_on_message"]
        from pytgbot.api_types.receivable.updates import Message
        self.assertIsInstance(msg, Message)
        self.assertEquals(msg.to_array(), self.data_cmd["message"])
    # end def

    def test_on_message2(self):
        @self.bot.on_message("text")
        def _callback_test_on_message2(msg):
            self.callbacks_status["_callback_test_on_message2"] = msg
        # end def

        self.app_test.post(self.update_path, data=json.dumps(self.data_cmd), content_type='application/json')

        self.assertIn("_callback_test_on_message2", self.callbacks_status, "@on_message('text') func executed")
        msg = self.callbacks_status["_callback_test_on_message2"]
        from pytgbot.api_types.receivable.updates import Message
        self.assertIsInstance(msg, Message)
        self.assertEquals(msg.to_array(), self.data_cmd["message"])
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
