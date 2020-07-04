#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging
from teleflask.server.extras.polling.sync import Telepoll

from somewhere import API_KEY

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


bot = Telepoll(api_key=API_KEY)


@bot.command("test")
def test(update, text):
    return "You tested with {arg!r}".format(arg=text)
# end def


@bot.on_message()
def test32(update):
    bot.bot.forward_message(10717954)


@bot.on_update()
def test2(update):
    pass
# end def


bot.run_forever()
