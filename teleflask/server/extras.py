# -*- coding: utf-8 -*-
from .base import TeleflaskBase
from .mixins import StartupMixin, BotCommandsMixin, UpdatesMixin, MessagesMixin

__author__ = 'luckydonald'
__all__ = ["TeleflaskCommands", "TeleflaskMessages", "TeleflaskUpdates", "TeleflaskStartup", "Teleflask"]


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


class Teleflask(StartupMixin, BotCommandsMixin, MessagesMixin, UpdatesMixin, TeleflaskBase):
    """
    This is the full package, including all provided mixins.

    You can use:
    
        Startup:
            - `app.add_startup_listener` to let the given function be called on server/bot startup
            - `app.remove_startup_listener` to remove the given function again
            - `@app.on_startup` decorator which does the same as add_startup_listener.
            See :class:`teleflask.mixins.StartupMixin` for complete information.

        Commands: 
            - `app.add_command` to add command functions
            - `app.remove_command` to remove them again.
            - `@app.command("command")` decorator as alias to `add_command`
            - `@app.on_command("command")` decorator as alias to `add_command`
            See :class:`teleflask.mixins.BotCommandsMixin` for complete information.

        Messages:
            - `app.add_message_listener` to add functions
            - `app.remove_message_listener` to remove them again.
            - `@app.on_message` decorator as alias to `add_message_listener`
            See :class:`teleflask.mixins.MessagesMixin` for complete information.
     
        Updates:
            - `app.add_update_listener` to add functions to be called on incoming telegram updates.
            - `app.remove_update_listener` to remove them again.
            - `@app.on_update` decorator doing the same as `add_update_listener`
            See :class:`teleflask.mixins.UpdatesMixin` for complete information.

    Execution order:
    
        It will first check for commands (`@command`), then for messages (`@on_message`) and 
        finally for update listeners (`@on_update`)

    Functionality is separated into mixin classes. This means you can plug together a class with just the functions you need.
    But we also provide some ready-build cases:    
        :class:`teleflask.extras.TeleflaskCommands`, :class:`teleflask.extras.TeleflaskMessages`,
        :class:`teleflask.extras.TeleflaskUpdates` and :class:`teleflask.extras.TeleflaskStartup`.
    """
    pass
# end class


class TeleflaskComplete(Teleflask):
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn('Warning: TeleflaskComplete is deprecated. Please use the Teleflask class.',
                      DeprecationWarning)
        super().__init__(*args, **kwargs)
    # end def