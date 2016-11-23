# -*- coding: utf-8 -*-
from .base import TeleflaskBase
from .mixins import StartupMixin, BotCommandsMixin, UpdatesMixin, MessagesMixin

__author__ = 'luckydonald'
__all__ = ["TeleflaskCommands", "TeleflaskMessages", "TeleflaskUpdates", "TeleflaskStartup", "TeleflaskComplete"]


class TeleflaskCommands(BotCommandsMixin, TeleflaskBase):
    """
    You can use:
     `app.add_command` to add functions
     `app.remove_command` to remove them again.
     `@app.command("command")` decorator as alias to `add_command`
     `@app.on_command("command")` decorator as alias to `add_command`

    See :class:`teleflask.mixins.BotCommandsMixin` for complete information.
    """
    pass
# end class


class TeleflaskMessages(MessagesMixin, TeleflaskBase):
    """
    You can use:
     `app.add_message_listener` to add functions
     `app.remove_message_listener` to remove them again.
     `@app.on_message` decorator as alias to `add_message_listener`

    See :class:`teleflask.mixins.MessagesMixin` for complete information.
    """
    pass
# end class


class TeleflaskUpdates(UpdatesMixin, TeleflaskBase):
    """
    You can use:
     `app.add_update_listener` to add functions to be called on incoming telegram updates.
     `app.remove_update_listener` to remove them again.
     `@app.on_update` decorator doing the same as `add_update_listener`

    See :class:`teleflask.mixins.UpdatesMixin` for complete information.
    """
    pass
# end class


class TeleflaskStartup(StartupMixin, TeleflaskBase):
    """
    You can use:
     `app.add_startup_listener` to let the given function be called on server/bot startup
     `app.remove_startup_listener` to remove the given function again
     `@app.on_startup` decorator which does the same as add_startup_listener.

    See :class:`teleflask.mixins.StartupMixin` for complete information.
    """
# end class


class TeleflaskComplete(StartupMixin, BotCommandsMixin, MessagesMixin, UpdatesMixin, TeleflaskBase):
    """
    You can use:
     `app.add_startup_listener` to let the given function be called on server/bot startup
     `app.remove_startup_listener` to remove the given function again
     `@app.on_startup` decorator which does the same as add_startup_listener.
     See :class:`teleflask.mixins.StartupMixin` for complete information.

     `app.add_update_listener` to add functions to be called on incoming telegram updates.
     `app.remove_update_listener` to remove them again.
     `@app.on_update` decorator doing the same as `add_update_listener`
     See :class:`teleflask.mixins.UpdatesMixin` for complete information.

     `app.add_message_listener` to add functions
     `app.remove_message_listener` to remove them again.
     `@app.on_message` decorator as alias to `add_message_listener`
     See :class:`teleflask.mixins.MessagesMixin` for complete information.

     `app.add_command` to add command functions
     `app.remove_command` to remove them again.
     `@app.command("command")` decorator as alias to `add_command`
     `@app.on_command("command")` decorator as alias to `add_command`
     See :class:`teleflask.mixins.BotCommandsMixin` for complete information.
    """
    pass
# end class
