# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

VERSION = "2.0.0.dev23"
__version__ = VERSION

from .server import Teleflask
from .server.blueprints import TBlueprint
from .server.utilities import abort_processing
