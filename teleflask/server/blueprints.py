# -*- coding: utf-8 -*-
from collections import OrderedDict
from functools import update_wrapper  # should be installed by flask

from luckydonaldUtils.logger import logging

from server.base import TeleflaskBase
from server.mixins import UpdatesMixin, MessagesMixin, BotCommandsMixin, StartupMixin
from teleflask import Teleflask

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class TBlueprintSetupState(object):
    """Temporary holder object for registering a blueprint with the
    application.  An instance of this class is created by the
    :meth:`~flask.Blueprint.make_setup_state` method and later passed
    to all register callback functions.
    """

    def __init__(self, blueprint, app, options, first_registration):
        #: a reference to the current application
        self.app = app

        #: a reference to the blueprint that created this setup state.
        self.blueprint = blueprint

        #: a dictionary with all options that were passed to the
        #: :meth:`~flask.Flask.register_tblueprint` method.
        self.options = options

        #: as blueprints can be registered multiple times with the
        #: application and not everything wants to be registered
        #: multiple times on it, this attribute can be used to figure
        #: out if the blueprint was registered in the past already.
        self.first_registration = first_registration
    # end def
# end class


class TBlueprint(object):
    warn_on_modifications = False

    def __init__(self, name):
        self.name = name
        self.deferred_functions = []
    # end def

    def register(self, teleflask, options, first_registration=False):
        """Called by :meth:`Flask.register_tblueprint` to register a blueprint
        on the application.  This can be overridden to customize the register
        behavior.  Keyword arguments from
        :func:`~flask.Flask.register_tblueprint` are directly forwarded to this
        method in the `options` dictionary.
        """
        self._got_registered_once = True
        self._teleflask = teleflask
        state = self.make_setup_state(teleflask, options, first_registration)
        #if self.has_static_folder:
        #    state.add_url_rule(self.static_url_path + '/<path:filename>',
        #                       view_func=self.send_static_file,
        #                       endpoint='static')

        for deferred in self.deferred_functions:
            deferred(state)
        # end for
    # end def
    
    def make_setup_state(self, teleflask, options, first_registration=False):
        """Creates an instance of :meth:`~flask.blueprints.BlueprintSetupState`
        object that is later passed to the register callback functions.
        Subclasses can override this to return a subclass of the setup state.
        """
        return TBlueprintSetupState(self, teleflask, options, first_registration)
    # end def

    def record(self, func):
        """Registers a function that is called when the blueprint is
        registered on the application.  This function is called with the
        state as argument as returned by the :meth:`make_setup_state`
        method.
        """
        if self._got_registered_once and self.warn_on_modifications:
            from warnings import warn
            warn(Warning('The teleflask blueprint was already registered once '
                         'but is getting modified now.  These changes '
                         'will not show up.'))
        self.deferred_functions.append(func)
    # end def

    def record_once(self, func):
        """Works like :meth:`record` but wraps the function in another
        function that will ensure the function is only called once.  If the
        blueprint is registered a second time on the application, the
        function passed is not called.
        """
        def wrapper(state):
            if state.first_registration:
                func(state)
        return self.record(update_wrapper(wrapper, func))
    # end def

    def add_startup_listener(self, func):
        """
        Like `StartupMixin.remove_startup_listener`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.app.add_startup_listener(func)
        )
        return func
    # end def

    def remove_startup_listener(self, func):
        """
        Like `StartupMixin.remove_startup_listener`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.remove_startup_listener(func)
        )
        return func
    # end def

    def add_command(self, command, function, exclusive=False):
        """
        Like `BotCommandsMixin.add_command`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.add_command(command, function, exclusive)
        )
    # end def

    def remove_command(self, command=None, function=None):
        """
        Like `BotCommandsMixin.remove_command`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.remove_command(command, function)
        )
    # end def

    def add_message_listener(self, function, required_keywords=None):
        """
        Like `MessagesMixin.add_message_listener`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.add_message_listener(function, required_keywords)
        )
    # end def

    def remove_message_listeners(self, func):
        """
        Like `MessagesMixin.remove_message_listeners`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.remove_message_listeners(func)
        )

    def add_update_listener(self, function, required_keywords=None):
        """
        Like `UpdatesMixin.add_update_listener`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.add_update_listener(function, required_keywords)
        )
    # end def

    def remove_update_listener(self, func):
        """
        Like `UpdatesMixin.remove_update_listener`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.remove_update_listener(func)
        )
    # end def
    
    @property
    def teleflask(self):
        if not self._got_registered_once:
            raise AssertionError('Not registered to an Teleflask instance yet.')
        # end if
        if not self._teleflask:
            raise AssertionError('No Teleflask instance yet. Did you register it?')
        # end if
        return self._teleflask

    @property
    def bot(self):
        return self.teleflask.bot
    # end def

    @property
    def username(self):
        return self.teleflask.username
    # end def

    @property
    def user_id(self):
        return self.teleflask.user_id
    # end def

    @staticmethod
    def msg_get_reply_params(update):
        return TeleflaskBase.msg_get_reply_params(update)

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
        return self.teleflask.send_messages(messages, reply_chat, reply_msg)
    # end def






