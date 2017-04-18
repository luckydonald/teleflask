# -*- coding: utf-8 -*-
from flask import Flask, Blueprint
from luckydonaldUtils.logger import logging
from example2.bot_stuff import bot

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)

app = Flask(__name__)
sub_app = Blueprint('test', __name__)

bot.init_app(app, blueprint=sub_app)
app.register_blueprint(sub_app)


@app.route("/test")
def test():
    return "yes"


if __name__ == "__main__":  # no nginx
    # "__main__" means, this python file is called directly.
    # not to be confused with "main" (because main.py) when called from from nginx
    app.run(host='0.0.0.0', debug=True, port=5000)  # python development server if no nginx
# end if