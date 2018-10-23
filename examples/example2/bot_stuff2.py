# -*- coding: utf-8 -*-
from flask import Flask

from teleflask.server.extras import PollingTeleflask

from somewhere import API_KEY

from luckydonaldUtils.logger import logging
logging.add_colored_handler(level=logging.DEBUG)

logger = logging.getLogger(__name__)
__author__ = 'luckydonald'

PROT = "http://"
HOST = "localhost"
PORT = 8082

app = Flask(__name__)
bot = PollingTeleflask(API_KEY, https=False, hostname=HOST+":"+str(PORT), debug_routes=True)
bot.init_app(app)



@bot.command("test")
def test(update, text):
    return "You tested with {arg!r}".format(arg=text)
# end def

@bot.on_update()
def test2(update):
    return None

app.run(HOST, PORT, True)