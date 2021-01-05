# teleflask
###### Version 1.0.1

A python telegram bot framework based on flask and pytgbot
Tested to work on python 3. Might work on python 2.

## Install
##### Python Package Index

```bash
pip install teleflask
```

#### Soon

Currently the source version (here on Github) is a work in progress version.
Great features are to come, including a Blueprint feature.
It is currently at version `2.0.0.dev23`, and will be `2`.`0`.`0` when released.

If you want to try it out already, run
```bash
pip install -e git://github.com/luckydonald/teleflask.git@v2.0.0.dev23#egg=teleflask
```
Sometimes it might additionally be available on PyPI
```bash
pip install teleflask==2.0.0.dev23
```

#### Soon: Proxy

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


## Usage

### Initalize

```python
from teleflask import Teleflask

bot = Teleflask(API_KEY, app)
```

or

```python
from teleflask import Teleflask

bot = Teleflask(API_KEY)
bot.init_app(app)
```

`app` being your flask app.

### Usage
```python
# use bot from initialize above
from teleflask.messages import TextMessage


@app.route("/")
def index():
    return "This is a normal Flask page."
# end def


# Register the /start command
@bot.command("start")
def start(update, text):
    # update is the update object. It is of type pytgbot.api_types.receivable.updates.Update
    # text is the text after the command. Can be empty. Type is str.
    return TextMessage("<b>Hello!</b> Thanks for using @" + bot.username + "!", parse_mode="html")
# end def


# register a function to be called for updates.
@bot.on_update
def foo(update):
    from pytgbot.api_types.receivable.updates import Update
    assert isinstance(update, Update)
    # do stuff with the update
    # you can use bot.bot to access the pytgbot.Bot's messages functions
    if not update.message:
        return
        # you could use @bot.on_message instead of this if.
    # end if
    if update.message.new_chat_member:
        return TextMessage("Welcome!")
    # end if
# end def

```


# Short documentation

Functions and classes are explained in the docstrings in the sourcecode.

## `Teleflask`

`Teleflask` is the full package, including all provided functionality.

### Components

Functionality is separated into mixin classes. This means you can plug together a class with just the functions you need.
The `Teleflask` class includes all of them.

#### Startup (`teleflask.mixins.StartupMixin`):
- `app.add_startup_listener` to let the given function be called on server/bot startup
- `app.remove_startup_listener` to remove the given function again
- `@app.on_startup` decorator which does the same as add_startup_listener.

#### Commands (`teleflask.mixins.BotCommandsMixin`):
- `app.add_command` to add command functions
- `app.remove_command` to remove them again.
- `@app.command("command")` decorator as alias to `add_command`
- `@app.on_command("command")` decorator as alias to `add_command`

#### Messages (`teleflask.mixins.MessagesMixin`):
- `app.add_message_listener` to add functions
- `app.remove_message_listener` to remove them again.
- `@app.on_message` decorator as alias to `add_message_listener`

#### Updates (`teleflask.mixins.UpdatesMixin`):
- `app.add_update_listener` to add functions to be called on incoming telegram updates.
- `app.remove_update_listener` to remove them again.
- `@app.on_update` decorator doing the same as `add_update_listener`

### Execution order:

It will first check for registered commands (`@command`),
next for messages listeners (`@on_message`) and
finally for update listeners (`@on_update`).

### Running bot commands

The normal `pytgbot`'s bot is available as `.bot` in your `Teleflask` instance:

```python
from teleflask import Teleflask

bot = Teleflask(API_KEY, app)
bot.bot.send_message('@luckydonald', 'It works :D')  # please don't spam me :D
```


# Deployment
This section is for myself, as I always forget.
You can ignore the deployment section.

### Development release

#### Increment <code>.dev<i>XYZ</i></code>

```bash
bump2version dev
# check that tag and every replacement is correct
make upload
```
