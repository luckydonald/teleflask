"""
All the exceptions teleflask defines itself.
"""


class AbortPlease(Exception):
    """
    Use to stop processing more events in listener functions with the following decorators
    - @bot.on_update
    - @bot.on_message
    - @bot.on_command
    """
    pass