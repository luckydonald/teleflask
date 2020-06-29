# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

import sys as _sys

VERSION = "2.0.0.dev21"
__version__ = VERSION

__all__ = [
    'VERSION', '__version__',
    # the ones we provide for easy toplevel access:
    'Teleserver', 'Teleflask', 'TBlueprint', 'abort_processing',
    # submodules:
   'server', 'exceptions', 'messages', 'new_messages', 'proxy',
]

from .server.core import Teleserver

if _sys.version_info.major >= 3 and _sys.version_info.minor >= 6:
    try:
        # we try to serve them as lazy imports
        import importlib as _importlib

        _module = _importlib.import_module('.sever', __name__)

        def __getattr__(name):
            if name not in ('Teleserver', 'Teleflask'):
                raise AttributeError(f'module {_module.__spec__.parent!r} has no attribute {name!r}')
            # end if
            imported = _importlib.import_module(name, _module.__spec__.parent)
            return imported
        # end def
    except Exception:
        # for some reason it failed, go back to importing it directly
        from .server.extras.flask import Teleflask
    # end if
else:
    # older python, go back to importing it directly
    from .server.extras.flask import Teleflask
# end if

from .server.blueprints import TBlueprint
from .server.utilities import abort_processing
