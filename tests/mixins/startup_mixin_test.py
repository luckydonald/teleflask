# -*- coding: utf-8 -*-
import os
import unittest

from flask import Flask
from luckydonaldUtils.logger import logging

from teleflask.server.mixins import StartupMixin

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class Foo(StartupMixin):
    def __init__(self, callback_status, *args, **kwargs):
        self.callback_status = callback_status
        super().__init__(*args, **kwargs)
    # end def

    def process_update(self, update):
        self.callback_status["process_update"] = update
    # end def


class SomeTestCase(unittest.TestCase):
    """
    `@app.on_startup` decorator
    `app.add_startup_listener(func)`
    `app.remove_startup_listener(func)`
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
        del self.mixin.startup_listeners
        del self.mixin
    # end def

    def test__on_startup__add_before_startup(self):
        self.assertNotIn("on_startup", self.callbacks_status, "not executed yet")
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")

        @self.mixin.on_startup
        def on_startup__callback():
            self.callbacks_status["on_startup"] = True
        # end def

        self.assertIn(on_startup__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertNotIn("on_startup", self.callbacks_status, "no data => not executed yet")

        self.mixin.do_startup()
        self.assertIn("on_startup", self.callbacks_status, "has data => executed")
    # end def

    def test__on_startup__add_after_startup(self):
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")
        self.assertNotIn("on_startup2", self.callbacks_status, "no data => not executed yet")

        self.mixin.do_startup()

        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")
        self.assertNotIn("on_startup2", self.callbacks_status, "no data => not executed yet")

        @self.mixin.on_startup
        def on_startup2__callback():
            self.callbacks_status["on_startup2"] = True
        # end def

        self.assertIn(on_startup2__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertIn("on_startup2", self.callbacks_status, "has data => executed")
    # end def

    def test__add_startup_listener__add_before_startup(self):
        self.assertNotIn("add_startup_listener", self.callbacks_status, "not executed yet")
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")

        def add_startup_listener__callback():
            self.callbacks_status["add_startup_listener"] = True
        # end def
        self.mixin.add_startup_listener(add_startup_listener__callback)

        self.assertIn(add_startup_listener__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertNotIn("add_startup_listener", self.callbacks_status, "no data => not executed yet")

        self.mixin.do_startup()
        self.assertIn("add_startup_listener", self.callbacks_status, "has data => executed")
    # end def

    def test__add_startup_listener__add_after_startup(self):
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")
        self.assertNotIn("add_startup_listener2", self.callbacks_status, "no data => not executed yet")

        self.mixin.do_startup()

        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")
        self.assertNotIn("add_startup_listener2", self.callbacks_status, "no data => not executed yet")

        def add_startup_listener2__callback():
            self.callbacks_status["add_startup_listener2"] = True
        # end def
        self.mixin.add_startup_listener(add_startup_listener2__callback)

        self.assertIn(add_startup_listener2__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertIn("add_startup_listener2", self.callbacks_status, "has data => executed")
    # end def
    
    def test__remove_startup_listener__before_execution(self):
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")
        self.assertNotIn("remove_startup_listener", self.callbacks_status, "no data => not executed yet")

        @self.mixin.on_startup
        def remove_startup_listener__callback():
            self.callbacks_status["remove_startup_listener"] = True
        # end def

        self.assertIn(remove_startup_listener__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertNotIn("remove_startup_listener", self.callbacks_status, "no data => not executed yet")

        self.mixin.remove_startup_listener(remove_startup_listener__callback)

        self.assertNotIn(remove_startup_listener__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertNotIn("remove_startup_listener", self.callbacks_status, "no data => not executed yet")

        self.mixin.do_startup()

        self.assertNotIn("remove_startup_listener", self.callbacks_status, "no data => not executed because deleted")
    # end def

    def test__remove_startup_listener__after_execution(self):
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")
        self.assertNotIn("remove_startup_listener2", self.callbacks_status, "no data => not executed yet")

        @self.mixin.on_startup
        def remove_startup_listener2__callback():
            self.callbacks_status["remove_startup_listener2"] = True

        # end def

        self.assertIn(remove_startup_listener2__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertNotIn("remove_startup_listener2", self.callbacks_status, "no data => not executed yet")

        self.mixin.do_startup()

        self.assertIn("remove_startup_listener2", self.callbacks_status, "data => already executed")
        self.assertIn(remove_startup_listener2__callback, self.mixin.startup_listeners, "in list => listener still here")

        self.mixin.remove_startup_listener(remove_startup_listener2__callback)

        self.assertNotIn(remove_startup_listener2__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertIn("remove_startup_listener2", self.callbacks_status, "data => already executed")
    # end def

    def test__process_update(self):
        self.assertNotIn("process_update", self.callbacks_status, "no data => not executed yet")
        from pytgbot.api_types.receivable.updates import Update
        update = Update(1000)
        self.mixin.process_update(update)
        self.assertIn("process_update", self.callbacks_status, "has data => executed")
        self.assertEqual(self.callbacks_status["process_update"], update, "same => data correct")
    # end def

    def test__do_startup__raising(self):
        self.assertNotIn("on_startup", self.callbacks_status, "not executed yet")
        self.assertFalse(self.mixin.startup_listeners, "empty listener list => not added yet")

        @self.mixin.on_startup
        def on_startup__callback():
            self.callbacks_status["on_startup"] = True
            raise ArithmeticError("Exception Test")
        # end def

        self.assertIn(on_startup__callback, self.mixin.startup_listeners, "in list => listener added")
        self.assertNotIn("on_startup", self.callbacks_status, "no data => not executed yet")

        with self.assertRaises(ArithmeticError, msg="exception raised"):
            self.mixin.do_startup()
        # end with
        self.assertIn("on_startup", self.callbacks_status, "has data => executed")
    # end def
# end class
