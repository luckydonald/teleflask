# -*- coding: utf-8 -*-
from .base import TeleflaskBase
from .mixins import StartupMixin, BotCommandsMixin, UpdatesMixin, MessagesMixin

__author__ = 'luckydonald'
__all__ = ["Teleflask"]


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

    def __init__(self, api_key, app=None, blueprint=None, hostname=None, hostpath=None, hookpath="/income/{API_KEY}",
                 debug_routes=False, disable_setting_webhook=False, return_python_objects=True):
        """
        A new Teleflask object.

        :param api_key: The key for the telegram bot api.
        :type  api_key: str

        :param app: The flask app if you don't like to call :meth:`init_app` yourself.
        :type  app: flask.Flask | None

        :param blueprint: A blueprint, where the telegram webhook (and the debug endpoints, see `debug_routes`) will be registered in.
                          Use if you don't like to call :meth:`init_app` yourself.
                          If not set, but `app` is, it will register any routes to the `app` itself.
                          Note: This is NOT a `TBlueprint` but a regular `flask` one!
        :type  blueprint: flask.Blueprint | None

        :param hostname: The hostname or IP (and maybe a port) where this server is reachable in the internet.
                         Specify the path with :param hostpath:
                         Used to calculate the webhook url.
                         Also configurable via environment variables. See calculate_webhook_url()
        :param hostpath: The host url the base of where this bot is reachable.
                         Examples: None (for root of server) or "/bot2"
                         Note: The webhook will only be set on initialisation.
                         Also configurable via environment variables. See calculate_webhook_url()
        :param hookpath: The endpoint of the telegram webhook.
                        Defaults to "/income/<API_KEY>"
                        Note: The webhook will only be set on initialisation.
                        Also configurable via environment variables. See calculate_webhook_url()
        :param debug_routes: Add extra url endpoints usefull for debugging. See setup_routes(...)

        :param disable_setting_webhook: Disable updating the webhook when starting. Useful for unit tests.

        :param return_python_objects: Enable return_python_objects in pytgbot. See pytgbot.bot.Bot
        """
        super().__init__(api_key, app, blueprint, hostname, hostpath, hookpath, debug_routes, disable_setting_webhook,
                         return_python_objects)

    # end def
# end class
