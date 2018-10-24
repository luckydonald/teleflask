# Changelog
## v2.0.0 - ~~2018-07-12~~ (not released yet)

#### ⚠️ Breaking changes:

- **renamed** `reply_id` to `reply_msg` and `reply_to` to `reply_chat` and
- **method signature change**: switched order to `reply_chat, reply_msg` (chat now first).
- **removed**: premade mixin-mixes `TeleflaskCommands`, `TeleflaskMessages`, `TeleflaskUpdates` and `TeleflaskStartup`.
    They were never used anyway.
    Either recreate them on your own, or use the `Teleflask` class.
    This will also make using the new `TBlueprints` more straightforward.
- **removed** `FileIDMessage`. This was a custom `DocumentMessage`, before they could do `file_id`.
    Use `DocumentMessage(file_id="...")` instead.

- **changed** url path of the debug routes to be prefixed by `/teleflask_debug`

##### This affects:

- parameters of `bot.send_message`, `bot.send_messages`.
- returned values from `bot.msg_get_reply_params`.
- usage of `FileIDMessage`.
- usage of `TeleflaskCommands`, `TeleflaskMessages`, `TeleflaskUpdates` and `TeleflaskStartup`.

#### Other changes

- Removed deprecated `TeleflaskComplete` class which is just the old name for the `Teleflask` class.
    Use `Teleflask` instead.
- Added `inline_query` peer support to automatic replying.
- Improved automatic replying to work on updates with `callback_query`.
- Added new `GameMessage` and `MediaGroupMessage` as automatic reply type.
- Now requires `pytgbot >= 4.0`.

#### Added **blueprint** mechanics:

So in any file you can now write
```python
# part.py
from teleflask import TBlueprint

part = TBlueprint('some name')

@part.command('test')
def foobar(update, msg):
    return "A message like ususal."
# end def
```

In your main file where you have your Teleflask instance you just have to register them.
```python
# main.py
from teleflask import Teleflask
from somefile import part

bot = Teleflask(API_KEY, app)
bot.register_blueprint(part)

# alternatively:

bot = Teleflask(API_KEY, app)

```

#### Stop processing
Raise `AbortPlease` to stop processing more events in listener functions.

Works with the following decorators:

- `@bot.on_update`
- `@bot.on_message`
- `@bot.on_command`

```py
from teleflask.exceptions import AbortPlease

@bot.on_command('test')
def cmd_text(update):
    raise AbortPlease()
# end if
```

#### Proxy

Added proxy script to test webhooks in local environments
without exposing you to the internet.

###### CLI proxy:

```bash
usage python -m teleflask.proxy [-h|--help] [--https] [--hookpath HOOKPATH] api_key host port

Pulls updates from telegram and shoves them into your app.

positional arguments:
  api_key              api key for the telegram API to use.
  host                 turn on https on the url
  port                 the port number

optional arguments:
  -h, --help           show this help message and exit
  --https              turn on https on the url
  --hookpath HOOKPATH  the path for the webhook (default: "/income/{API_KEY}")
```

```bash
python -m teleflask.proxy "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" localhost 8080
```

###### In Project:
Note, this just launches the aforementioned script, in a background process directly.
Please don't use it.

```py
from teleflask.server.extras import PollingTeleflask

app = Flask(__name__)
bot = PollingTeleflask(API_KEY, https=False, hostname="localhost:8080", debug_routes=True)
bot.init_app(app)

app.run("localhost", 8080, debug=True)
```


#### Small changes
- added `/teleflask_debug/routes` to inspect the registered routes.


## v1.0.1 - 2018-07-04
> (In this examples `bot` being a `Teleflask` instance, not `pytgbot`'s bot. That would be `bot.bot`.)

- renamed `bot.send_message(...)` to `bot.send_message(...)`, and yield the results.
    - this means you need to iterate over it, to send all the messages.
    - To keep backwards compatibility, there is still `bot.send_message` keeping the old behaviour, looping through the new function, and discarding the results.
- Now `bot.process_result(...)` will return the results of `bot.send_messages(...)` (of the `Message.send(...)`s) as list,
  so you can call the `process_result(...)` function directly with any `Message` and use the telegram responses right away.
- Fixed automatic replying to work on updates with `callback_query`.


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
        
