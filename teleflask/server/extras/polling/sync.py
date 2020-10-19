# -*- coding: utf-8 -*-
from pprint import pformat
from flask import request

from luckydonaldUtils.logger import logging
from pytgbot.exceptions import TgApiServerException

from pytgbot import Bot
from pytgbot.api_types import TgBotApiObject
from pytgbot.api_types.receivable.peer import User
from pytgbot.api_types.receivable.updates import Update
from pytgbot.exceptions import TgApiServerException

from ...core import Teleprocessor

__author__ = 'luckydonald'
__all__ = ["Telepoll"]
logger = logging.getLogger(__name__)

class Telepoll(Teleprocessor):
    please_do_stop: bool

    def __init__(
        self,
        api_key: str,
        return_python_objects: bool = True,
    ):
        """
        A simple bot interface polling the telegram servers repeatedly and using the Teleserver api to process the updates.
        This allows to use this system without the need for servers and webhooks.

        Just initialize it and call `.run_forever()`

        :param api_key: The key for the telegram bot api.
        :type  api_key: str

        :param return_python_objects: Enable return_python_objects in pytgbot. See pytgbot.bot.Bot
        """
        super().__init__(api_key, return_python_objects=return_python_objects)
        self.please_do_stop = False
        self.init_bot()
        self._offset = None
    # end def

    def init_bot(self):
        """
        Creates the bot, and retrieves information about the bot itself (username, user_id) from telegram.

        :return:
        """
        if not self._bot:  # so you can manually set it before calling `init_app(...)`,
            # e.g. a mocking bot class for unit tests
            self._bot = Bot(self._api_key, return_python_objects=self._return_python_objects)
        elif self._bot.return_python_objects != self._return_python_objects:
            # we don't have the same setting as the given one
            raise ValueError("The already set bot has return_python_objects {given}, but we have {our}".format(
                given=self._bot.return_python_objects, our=self._return_python_objects
            ))
        # end def
        myself = self._bot.get_me()
        if self._bot.return_python_objects:
            self._me = myself
        else:
            assert isinstance(myself, dict)
            self._me = User.from_array(myself["result"])
        # end if
    # end def

    def _foreach_update(self):
        """
        Waits for the next update by active polling the telegram servers.
        As soon as we got an update, it'll call all the registered @decorators, and will yield the results of those,
        so you can process them. If a single update triggers multiple results, all of those will be yielded.
        So you'd get sendable stuff, or None.

        :return:
        """

    def run_forever(self, remove_webhook: bool = True):
        if remove_webhook:
            self.bot.set_webhook('')
        # end if
        while not self.please_do_stop:
            updates = self.bot.get_updates(
                offset=self._offset,
                limit=100,
                error_as_empty = True,
            )
            for update in updates:
                logger.debug(f'processing update: {update!r}')
                self._offset = update.update_id
                try:
                    result = self.process_update(update)
                except:
                    logger.exception('processing update failed')
                    continue
                # end try
                try:
                     messages = self.process_result(update, result)
                except:
                    logger.exception('processing result failed')
                    continue
                # end try
                logger.debug(f'sent {"no" if messages is None else len(messages)} messages')
            # end for
        # end while
# end class
