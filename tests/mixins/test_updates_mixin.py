# -*- coding: utf-8 -*-
import os
import unittest

from flask import Flask
from luckydonaldUtils.logger import logging
from pytgbot.api_types.receivable.updates import Update

from teleflask.server.mixins import UpdatesMixin

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class Foo(UpdatesMixin):
    def __init__(self, callback_status, *args, **kwargs):
        self.callback_status = callback_status
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
        self.mixin = Foo(callback_status=self.callbacks_status)
        print(self.mixin)
    # end def

    def tearDown(self):
        print("tearDown")
        del self.callbacks_status
        del self.mixin.update_listeners
        del self.mixin
    # end def

    data_edit = Update.from_array({
        "update_id":10000,
        "edited_message": {
            "date":1441645532,
            "chat":{
                "last_name":"Test Lastname",
                "type": "private",
                "id":1111111,
                "first_name":"Test Firstname",
                "username":"Testusername"
            },
            "message_id":1365,
            "from":{
                "last_name":"Test Lastname",
                "id":1111111,
                "first_name":"Test Firstname",
                "username":"Testusername"
            },
            "text":"Edited text",
            "edit_date": 1441646600
        }
    })

    data_msg_with_reply = Update.from_array({
        "update_id":10000,
        "message":{
            "date":1441645532,
            "chat":{
                "last_name":"Test Lastname",
                "type": "private",
                "id":1111111,
                "first_name":"Test Firstname",
                "username":"Testusername"
            },
            "message_id":1365,
            "from":{
                "last_name":"Test Lastname",
                "id":1111111,
                "first_name":"Test Firstname",
                "username":"Testusername"
            },
            "text":"start",
            "reply_to_message":{
                "date":1441645000,
                "chat": {
                    "last_name":"Reply Lastname",
                    "type": "private",
                    "id":1111112,
                    "first_name":"Reply Firstname",
                    "username":"Testusername"
                },
                "message_id":1334,
                "text":"Original"
            }
        }
    })

    def test__on_update__all(self):
        self.assertNotIn("on_update", self.callbacks_status, "no data => not executed yet")
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        @self.mixin.on_update
        def on_update__callback(update):
            self.callbacks_status["on_update"] = update
            return update
        # end def

        self.assertIsNotNone(on_update__callback, "function is not None => decorator returned something")
        self.assertIn(on_update__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertNotIn("on_update", self.callbacks_status, "no data => not executed yet")

        self.mixin.process_update(self.data_msg_with_reply)

        self.assertIn("on_update", self.callbacks_status, "has data => did execute")
        self.assertEqual(self.callbacks_status["on_update"], self.data_msg_with_reply,
                         "has update => successfully executed given function")
        self.assertIn("processed_update", self.callbacks_status, "executed result collection")
        self.assertEqual(self.callbacks_status["processed_update"],
                         (self.data_msg_with_reply, self.data_msg_with_reply))  # update, result

        self.mixin.process_update(self.data_edit)

        self.assertIn("on_update", self.callbacks_status, "has data => did execute")
        self.assertEqual(self.callbacks_status["on_update"], self.data_edit,
                         "has update => successfully executed given function")
        self.assertIn("processed_update", self.callbacks_status, "executed result collection")
        self.assertEqual(self.callbacks_status["processed_update"], (self.data_edit, self.data_edit))  # update, result
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

    def test__on_update__exception(self):
        self.assertNotIn("on_update", self.callbacks_status, "no data => not executed yet")
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")
        self.callbacks_status["on_update_es"] = list()
        self.assertIn("on_update_es", self.callbacks_status, "just test setup")
        self.assertListEqual(self.callbacks_status["on_update_es"], [], "just test setup")

        @self.mixin.on_update
        def on_update__callback1(update):
            self.callbacks_status["on_update_e1"] = update
            self.callbacks_status["on_update_es"].append(1)
            return 1
        # end def

        @self.mixin.on_update
        def on_update__callback2(update):
            self.callbacks_status["on_update_e2"] = update
            self.callbacks_status["on_update_es"].append(2)
            raise ArithmeticError("Exception Test")
        # end def

        @self.mixin.on_update
        def on_update__callback3(update):
            self.callbacks_status["on_update_e3"] = update
            self.callbacks_status["on_update_es"].append(3)
            return 3
        # end def

        self.assertIsNotNone(on_update__callback1, "function 1 is not None => decorator returned something")
        self.assertIsNotNone(on_update__callback2, "function 2 is not None => decorator returned something")
        self.assertIsNotNone(on_update__callback3, "function 3 is not None => decorator returned something")
        self.assertIn(on_update__callback1, self.mixin.update_listeners, "1 in list => listener added")
        self.assertIn(on_update__callback2, self.mixin.update_listeners, "2 in list => listener added")
        self.assertIn(on_update__callback3, self.mixin.update_listeners, "3 in list => listener added")
        self.assertNotIn("on_update_e1", self.callbacks_status, "1 no data => 1 not executed yet")
        self.assertNotIn("on_update_e2", self.callbacks_status, "2 no data => 2 not executed yet")
        self.assertNotIn("on_update_e3", self.callbacks_status, "3 no data => 3 not executed yet")
        self.assertListEqual(self.callbacks_status["on_update_es"], [], "no data => all not executed yet")

        self.mixin.process_update(self.data_msg_with_reply)

        self.assertIn("on_update_e1", self.callbacks_status, "1 has data => 1 did execute")
        self.assertIn("on_update_e2", self.callbacks_status, "2 has data => 2 did execute")
        self.assertIn("on_update_e3", self.callbacks_status, "3 has data => 3 did execute")
        self.assertEqual(self.callbacks_status["on_update_e1"], self.data_msg_with_reply,
                         "1 has update => successfully called given function")
        self.assertEqual(self.callbacks_status["on_update_e2"], self.data_msg_with_reply,
                         "2 has update => successfully called given function")
        self.assertEqual(self.callbacks_status["on_update_e3"], self.data_msg_with_reply,
                         "3 has update => successfully called given function")
        self.assertIn("processed_update", self.callbacks_status,
                         "did execute processing updates => some function executed")
        self.assertListEqual(self.callbacks_status["on_update_es"], [1,2,3], "=> successfully executed")
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

        self.assertNotIn("on_update2", self.callbacks_status, "no data => not executed => filtered non-'edited_message'")
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
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update
        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

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
        self.assertListEqual(list(self.mixin.update_listeners.keys()), [add_update_listener__callback], "=> listener list correct")

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
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "=> listener list correct"
        )
        self.assertListEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [["edited_message"]],
            "listener filter list correct"
        )
        # add another update listener
        self.mixin.add_update_listener(add_update_listener__callback, ["message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "listener list still correct => no duplicates"
        )
        self.assertListEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [["edited_message"], ["message"]],  # [[AND] OR [AND]]
            "listener filter list correct => added keyword"
        )

        # add another update listener
        self.mixin.add_update_listener(add_update_listener__callback, ["message", "edited_message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "listener list still correct => no duplicates"
        )
        self.assertListEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [["edited_message"], ["message"], ["message", "edited_message"]],  # [[AND] OR [AND] OR ['' AND '']]
            "listener filter list correct => added keyword"
        )
    # end def

    def test__add_update_listener__no_duplicates__overwrite_unfiltered(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        # add unfiltered listener
        self.mixin.add_update_listener(add_update_listener__callback)

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "=> listener added to list correctly"
        )
        self.assertEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [None],
            "[] => listener unfiltered"
        )

        # add unfiltered listener again, this time with filter
        self.mixin.add_update_listener(add_update_listener__callback, ["message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "listener list still correct => no duplicates"
        )
        self.assertEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [None],
            "listener filter list still None => filter did not overwrite unfiltered"
        )
    # end def

    def test__add_update_listener__no_duplicates__unfiltered_overwrites(self):
        self.assertFalse(self.mixin.update_listeners, "empty listener list => not added yet")

        def add_update_listener__callback(update):
            self.callbacks_status["add_update_listener"] = update
            return update

        # end def

        self.assertFalse(self.mixin.update_listeners, "empty listener list => still not added")

        # add with filter
        self.mixin.add_update_listener(add_update_listener__callback, ["message"])

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener added")
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "listener list is correct"
        )
        self.assertListEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [["message"]],
            "listener filter list correct"
        )

        # add unfiltered
        self.mixin.add_update_listener(add_update_listener__callback)
        # should delete filter.

        self.assertIn(add_update_listener__callback, self.mixin.update_listeners, "in list => listener still added")
        self.assertListEqual(
            list(self.mixin.update_listeners.keys()),
            [add_update_listener__callback],
            "listener list still correct => no duplicates"
        )
        self.assertEqual(
            self.mixin.update_listeners[add_update_listener__callback],
            [None],
            "listener filter list now None => filter overwritten with unfiltered"
        )
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
