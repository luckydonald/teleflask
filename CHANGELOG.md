# Changelog
## v1.0.0
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

- Fixes in `messages`:
    - Let `MessageWithReplies` also return the results.
    - Allow `TypingMessage` to use the `TypingMessage.CANCEL`.

- specified minimum versions for some dependencies
    - `pytgbot>=2.3.3` (for the new webhooks)
    - `luckydonald-utils>=0.52` (needed `cut_paragraphs` in `messages.py`)
    - `backoff>=1.4.1` (for the example using the flask development server, see [backoff#30](https://github.com/litl/backoff/issues/30))
        
