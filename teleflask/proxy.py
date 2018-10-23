# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging
import requests
from pytgbot import Bot

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def proxy_telegram(api_key, https=False, host="localhost", hookpath="/income/{API_KEY}", full_url=None):
    logger.debug("https: {!r}, host: {!r}, hookpath: {!r}, full_url: {!r}".format(https, host, hookpath, full_url))
    if full_url is None:
        full_url = "http" + ("s" if https else "") + "://" + host + hookpath.format(API_KEY=api_key)
    # end if
    bot = Bot(api_key, return_python_objects=False)
    while True:
        last_update = 0
        result = bot.get_updates(offset=last_update, poll_timeout=1000)
        updates = result["result"]
        n = len(updates)
        for i, update in  enumerate(updates):
            last_update = update['update_id']
            logger.debug("Polling update ({i:03}/{n:03}|{l}):\n{u}\n{r!r}".format(
                r=update, i=i, n=n, l=last_update, u=full_url
            ))
            requests.post(
                full_url,
                json=update,
                headers={
                    'Content-Type': 'application/json', 'Cache-Control': 'no-cache'
                }
            )
        # end def
    # end for
# end def
