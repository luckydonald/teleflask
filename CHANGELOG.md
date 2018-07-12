# Changelog
## v2.0.0 - ~~2018-07-12~~ (not released yet)
- renamed `reply_id` to `reply_msg` and `reply_to` to `reply_chat` and
- switched order to `reply_chat, reply_msg` (chat now first).

This affects:

- parameters of `bot.send_message`, `bot.send_messages`
- returned values from `bot.msg_get_reply_params`

Also

- Removed class mixes: `TeleflaskCommands`, `TeleflaskMessages`, `TeleflaskUpdates`, `TeleflaskStartup`. They were never used anyway.
    Either recreate them on your own, or use the `Teleflask` class.
- Removed deprecated `TeleflaskComplete` class which is just the old name for the `Teleflask` class.
    Use `Teleflask` instead.

And added blueprint mechanics:

```python
# main.py
from teleflask import Teleflask
from somefile import part

bot = Teleflask(API_KEY, app)
bot.register_blueprint(part)
```

```python
# part.py
from teleflask import TBlueprint

part = TBlueprint('some name')

@part.command('test')
def foobar(update, msg):
    return "A message like ususal."
# end def
```

## v1.0.1 - 2018-07-04
> (In this examples `bot` being a `Teleflask` instance, not `pytgbot`'s bot. That would be `bot.bot`.)

- renamed `bot.send_message(...)` to `bot.send_message(...)`, and yield the results.
    - this means you need to iterate over it, to send all the messages.
    - To keep backwards compatibility, there is still `bot.send_message` keeping the old behaviour, looping through the new function, and discarding the results.
- Now `bot.process_result(...)` will return the results of `bot.send_messages(...)` (of the `Message.send(...)`s) as list,
  so you can call the `process_result(...)` function directly with any `Message` and use the telegram responses right away.
- Fixed automatic replying to work with messages with `callback_query`.


## v1.0.0 - 2017-11-17
- Not any longer subclasses `flask.Flask`. This was ugly, and bad.
    Now you initialize it like this:
    ```python    
    bot = Teleflask(API_KEY, app)
    ```
    or 
    ```python
    bot = Teleflask(API_KEY)
    bot.init_app(app)
    ```
    - renamed `TeleflaskComplete` to just `Teleflask`
    - Make it loadable via `.init_app(app)`
    
    - You can now import `Teleflask` from the root of the module directly.
        ```python
        from teleflask import Teleflask
        ```
    - Actual setting of the webhook can be disabled via `DISABLE_SETTING_TELEGRAM_WEBHOOK=True` in the flask config.
      This is probably only usefull for tests.

- Mixin overhaul
    - all
        - any list/dict used for storage is now defined in the `__init__` method, so that it won't be global part of the class any longer.
        - decorators where you can specify required params can now be used multible times to allow different fields to trigger the same function.
        - all listeners which depend on incomming `update`s will now always have the `update` as first parameter.

    - `StartupMixin`
        - Added `__init__` method to `StartupMixin`, else the lists were static.
        - Added unit testing of `StartupMixin`.

    - `UpdatesMixin` overhaul
        - Added `__init__` method to `UpdatesMixin`, else the dict were static.
        - Changed dict to be OrderedDict, to preverse order on pre 3.6 systems.
        - Fixed `@on_update` did not return the (new) function.
        - Changed `add_update_listener` to merge keywords.
            - this is relevant for `@on_update`, too.
        - Added unit tests for `UpdatesMixin`.
    - `MessagesMixin`
        - Fixed `@on_message` did not return the (new) function.
        - `@on_message` will now really provide the `update` as fist argument.
            This is now conform to all other listeners, and a part of already existing documentation.

- Fixes in `messages`:
    - Let `MessageWithReplies` also return the results.
    - Allow `TypingMessage` to use the `TypingMessage.CANCEL`.
    - Fixed `DocumentMessage` to respect the set `file_mime`, and in case of given `file_content`, use the filename part from either the `file_path` or the `file_url`.
    - Also unknown `PhotoMessage`s will now have a `*.unknown-file-type.png` suffix.
    - Fixed `teleflask.server.base.TeleflaskBase.process_result`, now also setting `reply_to` and `reply_id` for edits and in channels.

- specified minimum versions for some dependencies
    - `pytgbot>=2.3.3` (for the new webhooks)
    - `luckydonald-utils>=0.52` (needed `cut_paragraphs` in `messages.py`)
    - `backoff>=1.4.1` (for the example using the flask development server, see [backoff#30](https://github.com/litl/backoff/issues/30))
        
