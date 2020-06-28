# -*- coding: utf-8 -*-
import abc

from pytgbot import Bot
from pytgbot.api_types import TgBotApiObject
from pytgbot.exceptions import TgApiServerException
from pytgbot.api_types.receivable.updates import Update as TGUpdate
from luckydonaldUtils.logger import logging
from luckydonaldUtils.exceptions import assert_type_or_raise


__author__ = 'luckydonald'
logger = logging.getLogger(__name__)
