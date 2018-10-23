# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging
from teleflask import Teleflask
from somewhere import API_KEY
from flask import Flask


logger = logging.getLogger(__name__)
__author__ = 'luckydonald'


app = Flask(__name__)
bot = Teleflask(API_KEY)
bot.init_app(app)



@bot.command("test")
def test(update, text):
    return "You tested with {arg!r}".format(arg=text)
# end def


@bot.on_update()
def test2(update):
    pass
# end def


if __name__ == '__main__':
    app.run('localhost', 8085, True)
# end if