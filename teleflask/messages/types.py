# -*- coding: utf-8 -*-
from typing import Union, List

from luckydonaldUtils.logger import logging
from luckydonaldUtils.exceptions import assert_type_or_raise
from pytgbot.api_types.sendable.input_media import InputMediaPhoto, InputMediaVideo

from .base import MessageWithChatID, MessageWithinChat, MessageMixinParseMode
from pytgbot.bot import Bot

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class ChatActionMessage(MessageWithChatID):
    """
    Automatic wrapper around `send_chat_action(chat_id, action)`.

    https://core.telegram.org/bots/api#sendchataction
    """
    TYPING = "typing"
    RECORD_AUDIO = "record_audio"
    UPLOAD_AUDIO = "upload_audio"
    RECORD_VIDEO = "record_video"
    UPLOAD_VIDEO = "upload_video"
    RECORD_VIDEO_NOTE = "record_video_note"
    UPLOAD_VIDEO_NOTE = "upload_video_note"
    UPLOAD_DOCUMENT = "upload_document"
    UPLOAD_PHOTO = "upload_photo"
    SELECTING_GEO = "find_location"
    CANCEL = ""

    allowed_actions = (
        TYPING, RECORD_AUDIO, UPLOAD_AUDIO, RECORD_VIDEO, UPLOAD_VIDEO, RECORD_VIDEO_NOTE, UPLOAD_VIDEO_NOTE,
        UPLOAD_DOCUMENT, UPLOAD_PHOTO, SELECTING_GEO, CANCEL,
    )
    check_action_whitelist = True  # this could be turned off in emergency conditions,
    # in that case make sure to submit a pull request with fixes to `allowed_actions`.

    def __init__(
            self,
            action: str,
            chat_id: Union[str, int, None] = None,
    ):
        MessageWithChatID.__init__(self, chat_id)
        if self.check_action_whitelist and action not in self.allowed_actions:
            raise ValueError(f'Chat action {action!r} unknown.')
        # end if
        self.action = action
    # end def

    def send(
            self,
            bot: Bot,
            chat_id: Union[int, None] = None,
            reply_id: Union[int, None] = None
    ):
        return bot.send_chat_action(chat_id=self.chat_id, action=self.action)
    # end def
# end class


class MediaGroupMessage(MessageWithinChat):
    """
    Automatic wrapper around `send_media_group(chat_id, media, disable_notification=None, reply_to_message_id=None)`.

    https://core.telegram.org/bots/api#sendchataction
    """

    def __init__(
            self,
            media: List[Union[InputMediaPhoto, InputMediaVideo]],
            chat_id: Union[str, int, None] = None,
            reply_to_message_id: Union[int, None] = None,
            disable_notification: Union[bool, None] = False,
    ):
        assert_type_or_raise(media, list, tuple, parameter_name='media')
        this.media = media

        MessageWithinChat.__init__(
            self, chat_id=chat_id, reply_to_message_id=reply_to_message_id, disable_notification=disable_notification
        )
    # end def

    def send(
        self,
        bot: Bot,
        chat_id: Union[int, None] = None,
        reply_id: Union[int, None] = None
    ):
        return bot.send_media_group(
            chat_id=chat_id, media=this.media, **MessageWithinChat.kwargs(self)
        )
    # end def
# end class


class TextMessage(MessageWithinChat, MessageMixinParseMode):
    def __init__(
        self,
        text: str,
        chat_id: Union[str, int, None] = None,
        reply_to_message_id: Union[int, None] = None,
        disable_notification: Union[bool, None] = False,
        parse_mode: str = self.DEFAULT,
    ):
        assert_type_or_raise(text, str, parameter_name='text')
        this.text = text

        MessageWithinChat.__init__(
            self, chat_id=chat_id, reply_to_message_id=reply_to_message_id, disable_notification=disable_notification
        )
        MessageMixinParseMode.__init__(
            self, parse_mode=parse_mode,
        )
    # end def

    def send(
        self,
        bot: Bot,
        chat_id: Union[int, None] = None,
        reply_id: Union[int, None] = None
    ):
        return bot.send_message(
            text=this.text,
            chat_id=chat_id, reply_to_message_id=reply_id,
            **MessageMixinParseMode.kwargs(self),
            **MessageWithinChat.kwargs(self),
        )
    # end def
# end class


