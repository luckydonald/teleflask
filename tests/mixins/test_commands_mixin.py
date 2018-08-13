# -*- coding: utf-8 -*-
import os
import unittest

from flask import Flask
from luckydonaldUtils.logger import logging
from pytgbot.api_types.receivable.updates import Update

from teleflask.server.mixins import BotCommandsMixin

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class BotCommandsMixinMockup(BotCommandsMixin):
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

    def test__on_update__exception__single(self):
        self.assertNotIn("on_update", self.callbacks_status, "no data => not executed yet")
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        @self.mixin.on_update
        def on_update__callback(update):
            self.callbacks_status["on_update_e1"] = update
            raise ArithmeticError("Exception Test")

        # end def

        self.assertIsNotNone(on_update__callback, "function is not None => decorator returned something")
        self.assertIn(on_update__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertNotIn("on_update_e1", self.callbacks_status, "no data => not executed yet")

        self.mixin.process_update(self.data_msg_with_reply)

        self.assertIn("on_update_e1", self.callbacks_status, "has data => did execute")
        self.assertEqual(self.callbacks_status["on_update_e1"], self.data_msg_with_reply,
                         "has update => successfully called given function")
        self.assertNotIn("processed_update", self.callbacks_status,
                         "did not execute processing updates => exeption raised sucessfully")
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
        def on_command__callback1(update):
            self.callbacks_status["on_command_e1"] = update
            self.callbacks_status["on_command_es"].append(1)
            return 1
        # end def

        @self.mixin.command('start')
        def on_command__callback2(update):
            self.callbacks_status["on_command_e2"] = update
            self.callbacks_status["on_command_es"].append(2)
            raise ArithmeticError("Exception Test")
        # end def

        @self.mixin.command('start')
        def on_command__callback3(update):
            self.callbacks_status["on_command_e3"] = update
            self.callbacks_status["on_command_es"].append(3)
            return 3
        # end def

        self.assertIsNotNone(on_command__callback1, "function 1 is not None => decorator returned something")
        self.assertIsNotNone(on_command__callback2, "function 2 is not None => decorator returned something")
        self.assertIsNotNone(on_command__callback3, "function 3 is not None => decorator returned something")
        listeners = [(k, v) for k, v in self.mixin.commands.items()]
        print('l:', repr(listeners))
        print('s:', repr(('/start', (on_command__callback1, False))))
        print('b:', repr(('/start', (on_command__callback1, False)) in listeners))
        self.assertIn(('/start', (on_command__callback1, False)), listeners, "1 in list => listener added")
        self.assertIn(('/start', (on_command__callback2, False)), listeners, "2 in list => listener added")
        self.assertIn(('/start', (on_command__callback3, False)), listeners, "3 in list => listener added")
        self.assertNotIn("on_command_e1", self.callbacks_status, "1 no data => 1 not executed yet")
        self.assertNotIn("on_command_e2", self.callbacks_status, "2 no data => 2 not executed yet")
        self.assertNotIn("on_command_e3", self.callbacks_status, "3 no data => 3 not executed yet")
        self.assertListEqual(self.callbacks_status["on_command_es"], [], "no data => all not executed yet")

        return
        self.mixin.process_update(self.data_msg_with_reply)

        self.assertIn("on_command_e1", self.callbacks_status, "1 has data => 1 did execute")
        self.assertIn("on_command_e2", self.callbacks_status, "2 has data => 2 did execute")
        self.assertIn("on_command_e3", self.callbacks_status, "3 has data => 3 did execute")
        self.assertEqual(self.callbacks_status["on_command_e1"], self.data_msg_with_reply,
                         "1 has update => successfully called given function")
        self.assertEqual(self.callbacks_status["on_command_e2"], self.data_msg_with_reply,
                         "2 has update => successfully called given function")
        self.assertEqual(self.callbacks_status["on_command_e3"], self.data_msg_with_reply,
                         "3 has update => successfully called given function")
        self.assertIn("processed_update", self.callbacks_status,
                      "did execute processing updates => some function executed")
        self.assertListEqual(self.callbacks_status["on_command_es"], [1, 2, 3], "=> successfully executed")

    # end def

    def test__on_update__selective(self):
        self.assertNotIn("on_update2", self.callbacks_status, "no data => not executed yet")
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        @self.mixin.on_update("edited_message")
        def on_update2__callback(update):
            self.callbacks_status["on_update2"] = update
            return update

        # end def

        self.assertIsNotNone(on_update2__callback, "function is not None => decorator returned something")
        self.assertIn(on_update2__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertNotIn("on_update2", self.callbacks_status, "no data => not executed yet")

        self.mixin.process_update(self.data_msg_with_reply)

        self.assertNotIn("on_update2", self.callbacks_status,
                         "no data => not executed => filtered non-'edited_message'")
        self.assertNotIn("processed_update", self.callbacks_status,
                         "no result collected => filtered non-'edited_message'")

        self.mixin.process_update(self.data_edit)

        self.assertIn("on_update2", self.callbacks_status, "has data => did execute")
        self.assertEqual(self.callbacks_status["on_update2"], self.data_edit,
                         "has update => successfully executed given function")
        self.assertIn("processed_update", self.callbacks_status, "executed result collection")
        self.assertEqual(self.callbacks_status["processed_update"], (self.data_edit, self.data_edit))  # update, result

    # end def

    def test__add_update_listener__all(self):
        self.assertFalse(self.mixin.commands, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.commands, "empty listener list => still not added")

        self.mixin.add_update_listener(add_update_listener__callback)

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners,
                      "function in list => adding worked")

    # end def

    def test__add_update_listener__selective(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        self.mixin.add_update_listener(add_update_listener__callback, ["edited_message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners,
                      "function in list => adding worked")

    # end def

    def test__add_update_listener__no_duplicates(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        self.mixin.add_update_listener(add_update_listener__callback)

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "=> listener list correct")

        self.mixin.add_update_listener(add_update_listener__callback)

        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "listener list correct => no duplicates")

    # end def

    def test__add_update_listener__no_duplicates__add_keywords(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        self.mixin.add_update_listener(add_update_listener__callback, ["edited_message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "=> listener list correct")
        self.assertListEqual(self.mixin.update_listeners[add_update_listener__callback], ["edited_message"],
                             "listener filter list correct")

        self.mixin.add_update_listener(add_update_listener__callback, ["message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "listener list still correct => no duplicates")
        self.assertListEqual(self.mixin.update_listeners[add_update_listener__callback], ["edited_message", "message"],
                             "listener filter list correct => added keyword")

    # end def

    def test__add_update_listener__no_duplicates__overwrite_unfiltered(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        self.mixin.add_update_listener(add_update_listener__callback)

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "=> listener added to list correctly")
        self.assertEqual(self.mixin.update_listeners[add_update_listener__callback], None,
                         "None => listener unfiltered")

        self.mixin.add_update_listener(add_update_listener__callback, ["message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "listener list still correct => no duplicates")
        self.assertEqual(self.mixin.update_listeners[add_update_listener__callback], None,
                         "listener filter list still None => filter did not overwrite unfiltered")

    # end def

    def test__add_update_listener__no_duplicates__unfiltered_overwrites(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        self.mixin.add_update_listener(add_update_listener__callback, ["message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "listener list is correct")
        self.assertListEqual(self.mixin.update_listeners[add_update_listener__callback], ["message"],
                             "listener filter list correct")

        self.mixin.add_update_listener(add_update_listener__callback)

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback],
                             "listener list still correct => no duplicates")
        self.assertEqual(self.mixin.update_listeners[add_update_listener__callback], None,
                         "listener filter list now None => filter overwritten with unfiltered")

    # end def

    def test__remove_update_listener(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        @self.mixin.on_update
        def remove_update_listener__callback(update):
            pass

        # end def

        self.assertIn(remove_update_listener__callback, self.mixin.update_listeners, "in list => listener added")

        self.mixin.remove_update_listener(remove_update_listener__callback)

        self.assertFalse(self.mixin.update_listeners, "not in list => removed successfully")
        # end def

# end class
