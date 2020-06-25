# -*- coding: utf-8 -*-
from functools import update_wrapper  # should be installed by flask

from luckydonaldUtils.logger import logging

from .abstact import AbstractBotCommands, AbstractMessages, AbstractRegisterBlueprints, AbstractStartup, AbstractUpdates
from .base import TeleflaskBase
# from .mixins import UpdatesMixin, MessagesMixin, BotCommandsMixin, StartupMixin

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class TBlueprintSetupState(object):
    """Temporary holder object for registering a blueprint with the
    application.  An instance of this class is created by the
    :meth:`~teleflask.TBlueprint.make_setup_state` method and later passed
    to all register callback functions.
    """

    def __init__(self, tblueprint, teleflask, options, first_registration):
        #: a reference to the current application
        self.teleflask = teleflask

        #: a reference to the blueprint that created this setup state.
        self.tblueprint = tblueprint

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


class TBlueprint(AbstractBotCommands, AbstractMessages, AbstractRegisterBlueprints, AbstractStartup, AbstractUpdates):
    warn_on_modifications = False

    def __init__(self, name):
        self.name = name
        self.deferred_functions = []
        self._got_registered_once = False
    # end def

    def register(self, teleflask, options, first_registration=False):
        """Called by :meth:`Flask.register_tblueprint` to register a blueprint
        on the application.  This can be overridden to customize the register
        behavior.  Keyword arguments from
        :func:`~teleflask.Teleflask.register_blueprint` are directly forwarded to this
        method in the `options` dictionary.
        """
        self._got_registered_once = True
        self._teleflask = teleflask
        state = self.make_setup_state(teleflask, options, first_registration)
        for deferred in self.deferred_functions:
            deferred(state)
        # end for
    # end def

    def make_setup_state(self, teleflask, options, first_registration=False):
        """Creates an instance of :meth:`~flask.blueprints.BlueprintSetupState`
        object that is later passed to the register callback functions.
        Subclasses can override this to return a subclass of the setup state.
        """
        return TBlueprintSetupState(
            tblueprint=self, teleflask=teleflask, options=options, first_registration=first_registration
        )
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

    def register_tblueprint(self, tblueprint, **options):
        """
        Like `RegisterBlueprintsMixin.register_tblueprint`
        :param tblueprint:
        :param options:
        :return:
        """
        self.record(
            lambda state: state.teleflask.register_tblueprint(tblueprint, **options)
        )
        return None

    def add_startup_listener(self, func):
        """
        Like `StartupMixin.remove_startup_listener`, but for this `Blueprint`.
        """
        self.record(
            lambda state: state.teleflask.add_startup_listener(func)
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

    def on_startup(self, func):
        """
        Like `StartupMixin.on_startup`, but for this `Blueprint`.
        """
        return self.add_startup_listener(func)
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

    def on_command(self, command, exclusive=False):
        """
        Like `BotCommandsMixin.on_command`, but for this `Blueprint`.
        """
        return self.command(command, exclusive=exclusive)
    # end def

    def command(self, command, exclusive=False):
        """
        Like `BotCommandsMixin.command`, but for this `Blueprint`.
        """
        def register_command(func):
            self.add_command(command, func, exclusive=exclusive)
            return func
        return register_command
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

    def on_message(self, *required_keywords):
        """
        Like `MessagesMixin.on_message`, but for this `Blueprint`.
        """
        def on_message_inner(function):
            return self.add_message_listener(function, required_keywords=required_keywords)
        # end def

        if (len(required_keywords) == 1 and  # given could be the function, or a single required_keyword.
            not isinstance(required_keywords[0], str) # not string -> must be function
             ):
            # @on_message
            function = required_keywords[0]
            required_keywords = None
            return on_message_inner(function=function)  # not string -> must be function
        # end if
        # -> else: *required_keywords are the strings
        # @on_message("text", "sticker", "whatever")
        return on_message_inner  # let that function be called again with the function.
    # end def

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

    def on_update(self, *required_keywords):
        def on_update_inner(function):
            return self.add_update_listener(function, required_keywords=required_keywords)
        # end def
        if (len(required_keywords) == 1 and  # given could be the function, or a single required_keyword.
            not isinstance(required_keywords[0], str)  # not string -> must be function
             ):
            # @on_update
            function = required_keywords[0]
            required_keywords = None
            return on_update_inner(function)  # not string -> must be function
        # end if
        # -> else: *required_keywords are the strings
        # @on_update("update_id", "message", "whatever")
        return on_update_inner  # let that function be called again with the function.
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
        return self.teleflask.process_result(update, result)
    # end def
# end class
