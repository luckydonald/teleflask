# teleflask
A python telegram bot framework based on flask and pytgbot    
Version 0.0.8


## Usage

### Initalize

```python
from teleflask import Teleflask
```

```python
bot = Teleflask(API_KEY, app)
```
or 
```python
bot = Teleflask(API_KEY)
bot.init_app(app)
```


### Usage
```python
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

