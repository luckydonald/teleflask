# -*- coding: utf-8 -*-

from teleflask import Teleflask

from somewhere import API_KEY

from luckydonaldUtils.logger import logging

logger = logging.getLogger(__name__)
__author__ = 'luckydonald'


bot = Teleflask(API_KEY)


@bot.command("test")
def test(update, text):
    return "You tested with {arg!r}".format(arg=text)
# end def
