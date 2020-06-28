# -*- coding: utf-8 -*-
import os
import unittest

from flask import Flask
from luckydonaldUtils.logger import logging
from pytgbot.api_types.receivable.updates import Update

from teleflask.server.mixins import UpdatesMixin

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class BotCommandsMixinMockup(UpdatesMixin):
    def __init__(self, callback_status, *args, **kwargs):
        self.callback_status = callback_status  # extra dict for callbacks storage, to be checked by tests
        super().__init__(*args, **kwargs)

    # end def

    def process_result(self, update, result):
        """
        Give a process_result implementation,
        This would normal be added by :class:`TeleflaskMixinBase`.

        Here we just store the result in `self.callback_status`, for unit test checks.

        :param update: 'le Update.
        :return: None, in this case.
        """
        self.callback_status["processed_update"] = (update, result)
    # end def

    @property
    def username(self):
        return "UnitTest"
    # end def
# end class


class SomeUpdatesMixinTestCase(unittest.TestCase):
    """
    `@app.on_update` decorator
    `app.add_update_listener(func)`
    `app.remove_update_listener(func)`
    """

    def setUp(self):
        print("setUp")
        # Array to hold information about the called callbacks:
        self.callbacks_status = {}
        self.mixin = BotCommandsMixinMockup(callback_status=self.callbacks_status)
        print(self.mixin)
    # end def

    def tearDown(self):
        print("tearDown")
        del self.callbacks_status
        del self.mixin.commands
        del self.mixin
    # end def

    command_test = Update.from_array({
        "update_id": 4458,
        "message": {
            "message_id": 878,
            "from": {
                "id": 2,
                "first_name": "Test User",
                "username": "username",
                "language_code": "en"
            },
            "chat": {
                "id": 10717954,
                "first_name": "Luckydonald",
                "username": "luckydonald",
                "type": "private"
            },
            "date": 1495133903,
            "reply_to_message": {
                "message_id": 874,
                "from": {
                    "id": 10717954,
                    "first_name": "Luckydonald",
                    "username": "luckydonald",
                    "language_code": "en"
                },
                "chat": {
                    "id": 10717954,
                    "first_name": "Luckydonald",
                    "username": "luckydonald",
                    "type": "private"
                },
                "date": 1493146624,
                "text": "⁠⁠"
            },
            "text": "/test",
            "entities": [
                {
                    "type": "bot_command",
                    "offset": 0,
                    "length": 5
                }
            ]
        }
    })

    data_cmd_with_reply = Update.from_array({
        "update_id": 10000,
        "message": {
            "date": 1441645532,
            "chat": {
                "last_name": "Test Lastname",
                "type": "private",
                "id": 1111111,
                "first_name": "Test Firstname",
                "username": "Testusername"
            },
            "message_id": 1365,
            "from": {
                "last_name": "Test Lastname",
                "id": 1111111,
                "first_name": "Test Firstname",
                "username": "Testusername"
            },
            "text": "/test",
            "entities": [
                {
                    "type": "bot_command",
                    "offset": 0,
                    "length": 5
                }
            ],
            "reply_to_message": {
                "date": 1441645000,
                "chat": {
                    "last_name": "Reply Lastname",
                    "type": "private",
                    "id": 1111112,
                    "first_name": "Reply Firstname",
                    "username": "Testusername"
                },
                "message_id": 1334,
                "text": "Original"
            }
        }
    })

    def test__on_command__command(self):
        self.assertNotIn("on_command", self.callbacks_status, "no data => not executed yet")
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")

        @self.mixin.command('test')
        def on_command__callback(update, text):
            self.callbacks_status["on_command"] = update
            return update
        # end def

        self.assertIsNotNone(on_command__callback, "function is not None => decorator returned something")
        self.assertIn('/test', self.mixin.commands.keys(), 'command /test in dict keys => listener added')
        self.assertIn('/test@UnitTest', self.mixin.commands, 'command /test@{bot} in dict keys => listener added')
        self.assertEqual(self.mixin.commands['/test'], (on_command__callback, False), 'command /test has correct function')
        self.assertEqual(self.mixin.commands['/test@UnitTest'], (on_command__callback, False), 'command /test has correct function')
        self.assertNotIn("on_command", self.callbacks_status, "no data => not executed yet")

        self.mixin.process_update(self.command_test)

        self.assertIn("on_command", self.callbacks_status, "has data => did execute")
        self.assertEqual(self.callbacks_status["on_command"], self.command_test,
                         "has update => successfully executed given function")
        self.assertIn("processed_update", self.callbacks_status, "executed result collection")
        self.assertEqual(self.callbacks_status["processed_update"],
                         (self.command_test, self.command_test))  # update, result
    # end def

    def test__on_command__command_reply(self):
        self.assertNotIn("on_command", self.callbacks_status, "no data => not executed yet")
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")

        @self.mixin.command('test')
        def on_command__callback(update, text):
            self.callbacks_status["on_command"] = update
            return update

        # end def

        self.assertIsNotNone(on_command__callback, "function is not None => decorator returned something")
        self.assertIn('/test', self.mixin.commands.keys(), 'command /test in dict keys => listener added')
        self.assertIn('/test@UnitTest', self.mixin.commands, 'command /test@{bot} in dict keys => listener added')
        self.assertEqual(self.mixin.commands['/test'], (on_command__callback, False),
                         'command /test has correct function')
        self.assertEqual(self.mixin.commands['/test@UnitTest'], (on_command__callback, False),
                         'command /test has correct function')
        self.assertNotIn("on_command", self.callbacks_status, "no data => not executed yet")

        self.mixin.process_update(self.data_cmd_with_reply)

        self.assertIn("on_command", self.callbacks_status, "has data => did execute")
        self.assertEqual(self.callbacks_status["on_command"], self.data_cmd_with_reply,
                         "has update => successfully executed given function")
        self.assertIn("processed_update", self.callbacks_status, "executed result collection")
        self.assertEqual(self.callbacks_status["processed_update"],
                         (self.data_cmd_with_reply, self.data_cmd_with_reply))  # update, result
    # end def

    def test__on_command__no_duplicates(self):
        with self.assertRaises(AssertionError) as e:
            @self.mixin.command('start')
            def on_command__callback1(update):
                pass
            # end def

            @self.mixin.command('start')
            def on_command__callback2(update):
                pass
            # end def
        # end with
    # end def

    def test__on_command__exception(self):
        self.assertNotIn("on_command", self.callbacks_status, "no data => not executed yet")
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")
        self.callbacks_status["on_command_es"] = list()
        self.assertIn("on_command_es", self.callbacks_status, "just test setup, fail = broken test")
        self.assertListEqual(self.callbacks_status["on_command_es"], [], "just test setup, fail = broken test")

        @self.mixin.command('start')
        def on_command__callback1(update, text):
            self.callbacks_status["on_command_e1"] = update
            self.callbacks_status["on_command_es"].append(1)
            return 1
        # end def

        @self.mixin.command('start2')
        def on_command__callback2(update, text):
            self.callbacks_status["on_command_e2"] = update
            self.callbacks_status["on_command_es"].append(2)
            raise ArithmeticError("Exception Test")
        # end def

        @self.mixin.command('start23')
        def on_command__callback3(update, text):
            self.callbacks_status["on_command_e3"] = update
            self.callbacks_status["on_command_es"].append(3)
            return 3
        # end def

        self.assertIsNotNone(on_command__callback1, "function 1 is not None => decorator returned something")
        self.assertIsNotNone(on_command__callback2, "function 2 is not None => decorator returned something")
        self.assertIsNotNone(on_command__callback3, "function 3 is not None => decorator returned something")
        listeners = [(k, v) for k, v in self.mixin.commands.items()]

        self.assertIn(('/start', (on_command__callback1, False)), listeners, "1 in list => listener added")
        self.assertIn(('/start2', (on_command__callback2, False)), listeners, "2 in list => listener added")
        self.assertIn(('/start23', (on_command__callback3, False)), listeners, "3 in list => listener added")

        self.assertNotIn("on_command_e1", self.callbacks_status, "1 no data => 1 not executed yet")
        self.assertNotIn("on_command_e2", self.callbacks_status, "2 no data => 2 not executed yet")
        self.assertNotIn("on_command_e3", self.callbacks_status, "3 no data => 3 not executed yet")

        self.assertListEqual(self.callbacks_status["on_command_es"], [], "no data => all not executed yet")

        cmd2_update = Update.from_array(self.data_cmd_with_reply.to_array())
        cmd2_update.message.text = '/start2'
        cmd2_update.message.entities[0].length = cmd2_update.message.entities[0].length + 1

        print('>',str(cmd2_update.message))
        print('>',str(cmd2_update))
        print('>',str(cmd2_update.message.text))
        self.mixin.process_update(cmd2_update)

        print('c:', repr(self.callbacks_status))

        self.assertNotIn("on_command_e1", self.callbacks_status, "1 has data => 1 did execute")
        self.assertIn("on_command_e2", self.callbacks_status, "2 has data => 2 did execute")
        self.assertNotIn("on_command_e3", self.callbacks_status, "3 has data => 3 did execute")
        self.assertEqual(self.callbacks_status["on_command_e2"], cmd2_update, "2 has update => successfully called given function")
        self.assertNotIn("processed_update", self.callbacks_status, "did not execute commands, because exception => good")
        self.assertListEqual(self.callbacks_status["on_command_es"], [2], "=> successfully executed")
    # end def

    def test__remove_command_listener__by_command(self):
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")

        @self.mixin.command('foobar')
        def remove_command_listener__callback(update, text):
            pass
        # end def

        commands = [(k, v) for k, v in self.mixin.commands.items()]
        self.assertIn(('/foobar', (remove_command_listener__callback, False)), commands, "in list => listener added")
        self.assertIn(('/foobar@UnitTest', (remove_command_listener__callback, False)), commands, "in list => listener added")

        self.mixin.remove_command(command='foobar')

        commands = [(k, v) for k, v in self.mixin.commands.items()]
        self.assertNotIn(('/foobar', (remove_command_listener__callback, False)), commands, "not in list => listener removed")
        self.assertNotIn(('/foobar@UnitTest', (remove_command_listener__callback, False)), commands, "in list => only /foobar removed")

        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => removed successfully")
    # end def

    def test__remove_command_listener__by_function(self):
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")

        @self.mixin.command('foobar')
        def remove_command_listener__callback(update, text):
            pass
        # end def

        commands = [(k, v) for k, v in self.mixin.commands.items()]
        self.assertIn(('/foobar', (remove_command_listener__callback, False)), commands, "in list => listener added")
        self.assertIn(('/foobar@UnitTest', (remove_command_listener__callback, False)), commands, "in list => listener added")

        self.mixin.remove_command(function=remove_command_listener__callback)

        commands = [(k, v) for k, v in self.mixin.commands.items()]
        self.assertNotIn(('/foobar', (remove_command_listener__callback, False)), commands, "not in list => listener removed")
        self.assertNotIn(('/foobar@UnitTest', (remove_command_listener__callback, False)), commands, "in list => only /foobar removed")

        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => removed successfully")
    # end def

    def test__remove_nonexistent_command_listener__by_command(self):
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")
        self.mixin.remove_command(command="nothing")
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")
    # end def

    def test__remove_nonexistent_command_listener__by_function(self):
        def some_unregistered_func():
            pass
        # end def
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")
        self.mixin.remove_command(command=some_unregistered_func)
        self.assertDictEqual(self.mixin.commands, {}, "empty listener list => not added yet")
    # end def

    def test__remove_command_listener__by_none(self):
        with self.assertRaises(ValueError) as e:
            self.mixin.remove_command()
        # end if
    # end def
# end class
