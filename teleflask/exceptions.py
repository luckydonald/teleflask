"""
All the exceptions teleflask defines itself.
"""


class AbortProcessingPlease(Exception):
    """
    Use to stop processing more events in listener functions with the following decorators
    - @bot.on_update
    - @bot.on_message
    - @bot.on_command

    You can provide a `return_value`, which is processed like the normal `return return_value` statement.
    """

    def __init__(self, *args, return_value=None, **kwargs: object) -> None:
        """
        :param return_value: Similar to the normal return statement, this value get's processed by the bot,
                             and send to the chat.
        """
        super().__init__(*args, **kwargs)
        self.return_value = return_value
    # end def
# end class
