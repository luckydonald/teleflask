"""
All the exceptions teleflask defines itself.
"""


class AbortPlease(Exception):
    """
    Use to stop processing more events in listener functions with the following decorators
    - @bot.on_update
    - @bot.on_message
    - @bot.on_command

    You can store return_value, which is similar to `return return_value`.
    """

    def __init__(self, *args, return_value=None, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.return_value = return_value
    # end def
# end class
