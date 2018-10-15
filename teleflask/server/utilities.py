# -*- coding: utf-8 -*-
import logging

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
