# -*- coding: utf-8 -*-

import requests
from pytgbot import Bot
from pytgbot.api_types.receivable import WebhookInfo
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def proxy_telegram(api_key, https=False, host="localhost", hookpath="/income/{API_KEY}", full_url=None):
    logger.debug("https: {!r}, host: {!r}, hookpath: {!r}, full_url: {!r}".format(https, host, hookpath, full_url))
    if full_url is None:
        full_url = "http" + ("s" if https else "") + "://" + host + hookpath.format(API_KEY=api_key)
    # end if
    bot = Bot(api_key, return_python_objects=False)
    if bot.get_webhook_info()["result"]["url"] == "":
        logger.info("Webhook unset correctly. No need to change.")
    else:
        logger.debug(bot.delete_webhook())
    # end def
    last_update = 0
    while True:
        result = bot.get_updates(offset=last_update, poll_timeout=1000)
        updates = result["result"]
        n = len(updates)
        for i, update in  enumerate(updates):
            last_update = update['update_id'] + 1
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


if __name__ == '__main__':
    import argparse
    from luckydonaldUtils.logger import logging
    logging.add_colored_handler(level=logging.DEBUG)


    parser = argparse.ArgumentParser(description='Pulls updates from telegram and shoves them into your app.')
    parser.add_argument('api_key', action='store',
                        help='api key for the telegram API to use.')
    parser.add_argument('--https', action='store_true',
                        help='turn on https on the url')
    parser.add_argument('host', action='store',
                        help='turn on https on the url')
    parser.add_argument('port', type=int, action='store',
                        help='the port number')
    parser.add_argument('--hookpath', action='store', default="/income/{API_KEY}",
                        help='the path for the webhook (default: "/income/{API_KEY}")')

    args = parser.parse_args()
    proxy_telegram(api_key=args.api_key, https=args.https, host=args.host + ":" + str(args.port), hookpath=args.hookpath)
# end if
