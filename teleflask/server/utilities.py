# -*- coding: utf-8 -*-
import logging

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
