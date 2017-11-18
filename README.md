# teleflask
A python telegram bot framework based on flask and pytgbot    
Version 1.0.0


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




