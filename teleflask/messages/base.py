__all__ = []
from typing import Union, AnyStr
from pytgbot.bot import Bot

bot = Bot('asd')

class MessageBase(object):
    """ This is the base class of all the Message types in this class """
    pass
# end class

class MessageMixin(MessageBase):
    """ base class for all mixins """
    pass
# end class

class MessageWithChatID(MessageBase):
    def __init__(
            self,
            chat_id: Union[str, int] = None,
    ):
        """
        Parameters:

        :param chat_id: Unique identifier for the target chat or username of the target chat (@username)
        :type  chat_id: int | str|unicode
        """
        super().__init__()
        this.chat_id = chat_id
    # end def
# end def


class MessageWithinChat(MessageWithChatID):
    def __init__(
            self,
            chat_id: Union[str, int, None] = None,
            reply_to_message_id: Union[int, None] = None,
            disable_notification: Union[bool, None] = False
    ):
        """
        Parameters:

        :param chat_id: Unique identifier for the target chat or username of the target chat (@username)
        :type  chat_id: int | str|unicode
        """
        MessageWithChatID.__init__(self, chat_id=chat_id)
        self.reply_to_message_id = reply_to_message_id
        self.disable_notification = disable_notification
    # end def

    def kwargs(self):
        """ returns itself as dict """
        return {
            'reply_to_message_id': self.reply_to_message_id,
            'disable_notification': self.disable_notification,
        }
    # end def
# end class


class MessageWithReplyMarkup(MessageWithinChat):
    def __init__(
            self,
            chat_id: Union[str, int, None] = None,
            reply_to_message_id: Union[int, None] = None,
            disable_notification: Union[bool, None] = False
    ):
        """
        Parameters:

        :param chat_id: Unique identifier for the target chat or username of the target chat (@username)
        :type  chat_id: int | str|unicode
        """
        MessageWithChatID.__init__(self, chat_id=chat_id)
        self.reply_to_message_id = reply_to_message_id
        self.disable_notification = disable_notification
    # end def
# end def


class MessageMixinParseMode(MessageMixin):
    TEXT = 'text'
    HTML = 'html'
    MARKDOWN = 'markdown'
    DEFAULT = TEXT

    allowed_parse_modes = (TEXT, HTML, MARKDOWN, '',)
    check_parse_mode_whitelist = True  # this could be turned off in emergency conditions,
    # in that case make sure to submit a pull request with fixes to `allowed_parse_modes`.

    def __init__(
            self,
            parse_mode: str = DEFAULT
    ):
        if parse_mode == '':
            parse_mode = self.DEFAULT
        # end if
        if self.check_parse_mode_whitelist and parse_mode not in self.allowed_parse_modes:
            raise ValueError(f'Parse mode {parse_mode!r} unknown.')
        # end if
        self.parse_mode = parse_mode
        super().__init__()
    # end def

    def kwargs(self):
        """ returns itself as dict """
        return {
            'parse_mode': self.reply_to_message_id,
        }
    # end def
# end class
