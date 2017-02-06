# teleflask
A python telegram bot framework based on flask and pytgbot    
Version 0.0.8


## Usage

```python
from teleflask.server import TeleflaskComplete
from teleflask.messages import TextMessage

from somewhere import API_KEY  # I import it from some file which is kept private, not in git.
# Just set API_KEY = "your-api-key".

app = TeleflaskComplete(__name__, API_KEY)  # instead of writing:  app = Flask(__name__)


@app.route("/")
def index():
    return "This is a normal Flask page."
# end def


# Register the /start command
@app.command("start")
def start(update, text):
    # update is the update object. It is of type pytgbot.api_types.receivable.updates.Update
    # text is the text after the command. Can be empty. Type is str.
    return TextMessage("<b>Hello!</b> Thanks for using @" + app.username + "!", parse_mode="html")
# end def


# register a function to be called for updates.
@app.on_update
def foo(update):
    from pytgbot.api_types.receivable.updates import Update
    assert isinstance(update, Update)
    # do stuff with the update
    # you can use app.bot to access the bot's messages functions
    if not update.message:
        return
        # you could use @app.on_message instead of this if.
    # end if
    if update.message.new_chat_member:
        return TextMessage("Welcome!")
    # end if
# end def

```

