# -*- coding: utf-8 -*-
import logging
from typing import Union, Tuple

from ..exceptions import AbortProcessingPlease

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def _class_self_decorate(decorator_name):
    """
    Adds self to a decorator of a class when it must be used on functions of the same class.
    This is to be able to use it already before the class is completely parsed.

    >>> class Foo():
    >>>    def jsonify(self, func):
    >>>        print("value = " + str(self.value))
    >>>        return func
    >>>    # end def
    >>>
    >>>    @_class_self_decorate("jsonify")
    >>>    def bar(self):
    >>>        pass

    You can even prepare it before usage, outside of the class:

    >>> _self_jsonify = _class_self_decorate("jsonify")
    >>>
    >>> class Foo():
    >>>    def jsonify(self, func):
    >>>        print("value = " + str(self.value))
    >>>        return func
    >>>    # end def
    >>>
    >>>    @_self_jsonify
    >>>    def bar(self):
    >>>        pass
    :param decorator:
    :return:
    """
    from functools import wraps

    def func_extractor(func):
        @wraps(func)
        def self_extractor(self, *args):
            return getattr(self, decorator_name)(func)(self, *args)
        # end def
        return self_extractor
    # end def
    return func_extractor
# end def


def calculate_webhook_url(
    api_key: str,
    hostname: Union[str, None] = None,
    hostpath: Union[str, None] = None,
    hookpath: str = "/income/{API_KEY}"
) -> Tuple[str, str]:
    """
    Calculates the webhook url.
    Returns a tuple of the hook path (the url endpoint for your flask app) and the full webhook url (for telegram)
    Note: Both can include the full API key, as replacement for ``{API_KEY}`` in the hookpath.

    :Example:

    Your bot is at ``https://example.com:443/bot2/``,
    you want your flask to get the updates at ``/tg-webhook/{API_KEY}``.
    This means Telegram will have to send the updates to ``https://example.com:443/bot2/tg-webhook/{API_KEY}``.

    You now would set
        hostname = "example.com:443",
        hostpath = "/bot2",
        hookpath = "/tg-webhook/{API_KEY}"

    Note: Set ``hostpath`` if you are behind a reverse proxy, and/or your flask app root is *not* at the web server root.


    :param hostname: A hostname. Without the protocol.
                     Examples: "localhost", "example.com", "example.com:443"
                     If None (default), the hostname comes from the URL_HOSTNAME environment variable, or from http://ipinfo.io if that fails.
    :param hostpath: The path after the hostname. It must start with a slash.
                     Use this if you aren't at the root at the server, i.e. use url_rewrite.
                     Example: "/bot2"
                     If None (default), the path will be read from the URL_PATH environment variable, or "" if that fails.
    :param hookpath: Template for the route of incoming telegram webhook events. Must start with a slash.
                     The placeholder {API_KEY} will replaced with the telegram api key.
                     Note: This doesn't change any routing. You need to update any registered @app.route manually!
    :return: the tuple of calculated (hookpath, webhook_url).
    :rtype: tuple
    """
    import os, requests

    # #
    # #  try to fill out empty arguments
    # #
    if not hostname:
        hostname = os.getenv('URL_HOSTNAME', None)
    # end if
    if hostpath is None:
        hostpath = os.getenv('URL_PATH', "")
    # end if
    if not hookpath:
        hookpath = "/income/{API_KEY}"
    # end if

    # #
    # #  check if the path looks at least a bit valid
    # #
    logger.debug("hostname={hostn!r}, hostpath={hostp!r}, hookpath={hookp!r}".format(
        hostn=hostname, hostp=hostpath, hookp=hookpath
    ))
    if hostname:
        if hostname.endswith("/"):
            raise ValueError("hostname can't end with a slash: {value}".format(value=hostname))
        # end if
        if hostname.startswith("https://"):
            hostname = hostname[len("https://"):]
            logger.warning("Automatically removed \"https://\" from hostname. Don't include it.")
        # end if
        if hostname.startswith("http://"):
            raise ValueError("Don't include the protocol ('http://') in the hostname. "
                             "Also telegram doesn't support http, only https.")
        # end if
    else:
        raise ValueError("hostname can't be None.")
    # end if

    if not hostpath == "" and not hostpath.startswith("/"):
        logger.info("hostpath didn't start with a slash: {value!r} Will be added automatically".format(value=hostpath))
        hostpath = "/" + hostpath
    # end def
    if not hookpath.startswith("/"):
        raise ValueError("hookpath must start with a slash: {value!r}".format(value=hostpath))
    # end def
    hookpath = hookpath.format(API_KEY=api_key)
    if not hostpath:
        logger.info("URL_PATH is not set.")
    # end if
    webhook_url = "https://{hostname}{hostpath}{hookpath}".format(hostname=hostname, hostpath=hostpath, hookpath=hookpath)
    logger.debug("host={hostn!r}, hostpath={hostp!r}, hookpath={hookp!r}, hookurl={url!r}".format(
        hostn=hostname, hostp=hostpath, hookp=hookpath, url=webhook_url
    ))
    return hookpath, webhook_url
# end def


def abort_processing(func):
    """
    Wraps a function to automatically raise a `AbortProcessingPlease` exception after execution,
    containing the returned value of the function automatically.
    """
    def abort_inner(*args, **kwargs):
        return_value = func(*args, **kwargs)
        raise AbortProcessingPlease(return_value=return_value)
    # end def

    return abort_inner
# end def
