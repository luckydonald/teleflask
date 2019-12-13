#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod, ABCMeta
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'
__all__ = ['AbstractBotCommands', 'AbstractMessages', 'AbstractRegisterBlueprints', 'AbstractStartup', 'AbstractUpdates']

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class AbstractUpdates(metaclass=ABCMeta):
    @abstractmethod
    def on_update(self, *required_keywords):
        pass
    # end def

    @abstractmethod
    def add_update_listener(self, function, required_keywords=None):
        pass
    # end def

    @abstractmethod
    def remove_update_listener(self, func):
        pass
    # end def
# end class


class AbstractBotCommands(metaclass=ABCMeta):
    def on_command(self, command, exclusive=False):
        pass
    # end def

    @abstractmethod
    def command(self, command, exclusive=False):
        pass
    # end def

    @abstractmethod
    def add_command(self, command, function, exclusive=False):
        pass
    # end def

    @abstractmethod
    def remove_command(self, command=None, function=None):
        pass
    # end def
# end class


class AbstractMessages(metaclass=ABCMeta):
    @abstractmethod
    def on_message(self, *required_keywords):
        pass
    # end def

    @abstractmethod
    def add_message_listener(self, function, required_keywords=None):
        pass
    # end def

    @abstractmethod
    def remove_message_listeners(self, func):
        pass
    # end def
# end class


class AbstractRegisterBlueprints(metaclass=ABCMeta):
    @abstractmethod
    def register_tblueprint(self, tblueprint, **options):
        pass
    # end def
# end class


class AbstractStartup(metaclass=ABCMeta):
    @abstractmethod
    def on_startup(self, func):
        pass
    # end def

    @abstractmethod
    def add_startup_listener(self, func):
        pass
    # end def

    @abstractmethod
    def remove_startup_listener(self, func):
        pass
    # end def
# end class
