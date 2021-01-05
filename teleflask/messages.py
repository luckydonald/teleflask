# -*- coding: utf-8 -*-
import re
import os  # file existence check before upload.
import magic  # pip install python-magic   or   pip install python-magic-bin
import logging
import backoff
import requests
import mimetypes

from urllib.parse import urlparse

from DictObject import DictObject
from luckydonaldUtils.encoding import unicode_type
from luckydonaldUtils.decorators import deprecated

from luckydonaldUtils.exceptions import assert_type_or_raise as assert_instance
from luckydonaldUtils.files.mime import get_file_mime
from luckydonaldUtils.functions import caller
from luckydonaldUtils.text import text_split, cut_paragraphs, escape

from pytgbot import Bot as PytgbotApiBot
from pytgbot.api_types.receivable.updates import Message as PytgbotApiMessage
from pytgbot.api_types.sendable.files import InputFile, InputFileFromDisk, InputFileFromURL, InputFileFromBlob
from pytgbot.api_types.sendable.input_media import InputMedia, InputMediaPhoto, InputMediaVideo
from pytgbot.exceptions import TgApiServerException

__all__ = [
    "TypingMessage", "HTMLMessage", "DocumentMessage", "ImageMessage", "ForwardMessage",
    "GameMessage", "PlainMessage", "MarkdownMessage", "MessageWithReplies", "Message",
    "PhotoMessage", "StickerMessage", "MediaGroupMessage", "AudioMessage",
    "DEFAULT_MESSAGE_ID", "MAX_TEXT_LENGTH", "MAX_CAPTION_LENGTH",
]

from luckydonaldUtils.exceptions import assert_type_or_raise
__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 4096
MAX_CAPTION_LENGTH = 4096

RE_TG_USERNAME = r"((^|\s*)@(?P<username>(?:[a-z](?:[a-z0-9]|_(?!_)){3,}[a-z0-9])|" \
                 r"(?:gif|vid|wiki|pic|bing|imdb|bold))(\s*|$))"  # https://regex101.com/r/gS5lZ6/2
RE_TOO_MANY_REQUESTS = r"Too Many Requests: retry after (\d+)"


class DEFAULT_MESSAGE_ID(object):
    """
    Used for reply_id.
    """
    pass
# end class


class DoRetryException(BaseException):
    """
    Exception which will cause the backoff module to retry
    Used for backoff strategy
    """
    pass
# end class DoRetryException


class Message(object):
    def _apply_update_receiver(self, receiver, reply_id):
        """
        Updates `self.receiver` and/or `self.reply_id` if they still contain the default value.
        :param receiver: The receiver `chat_id` to use.
                         Either `self.receiver`, if set, e.g. when instancing `TextMessage(receiver=10001231231, ...)`,
                         or the `chat.id` of the update context, being the id of groups or the user's `from_peer.id` in private messages.
        :type  receiver: None | str|unicode | int


        :param reply_id: Reply to that `message_id` in the chat we send to.
                         Either `self.reply_id`, if set, e.g. when instancing `TextMessage(reply_id=123123, ...)`,
                         or the `message_id` of the update which triggered the bot's functions.
        :type  reply_id: Type[DEFAULT_MESSAGE_ID] | int
        """
        if self.receiver is None:
            self.receiver = receiver
        # end if
        if self.reply_id == DEFAULT_MESSAGE_ID:
            self.reply_id = reply_id
        # end if
    # end def


    def toString(self):
        assert (self.is_empty() != self.is_not_empty())
        text = "Empty " if not self.is_not_empty() else ""
        text_parts = []
        if hasattr(self, "text") and self.text:
            text_parts.append("text: \"%s\"" % (self.text.replace("\n", "\\n")))
        if hasattr(self, "file_id") and self.file_id:
            text_parts.append("file_id: \"%s\"" % (self.file_id))
        if hasattr(self, "file_url") and self.file_url:
            text_parts.append("file_url: \"%s\"" % (self.file_url))
        if hasattr(self, "file_path") and self.file_path:
            text_parts.append("file_path: \"%s\"" % (self.file_path))
        if hasattr(self, "fwd_msg_no") and self.fwd_msg_no:
            text_parts.append("fwd_msg_no: %s" % (self.fwd_msg_no))
        if hasattr(self, "receiver") and self.receiver:
            text_parts.append("receiver: %s" % (self.receiver))
        if hasattr(self, "reply") and self.reply:
            text_parts.append("reply: %s" % (self.reply))
        if hasattr(self, "_next_msg") and self._next_msg:
            text_parts.append("_next_msg: %s" % repr(self._next_msg))
        text += "Response {" + (", ".join(text_parts)) + "}"
        return text

    def is_empty(self):
        return not self.is_not_empty()

    def is_not_empty(self):
        if hasattr(self, "text") and self.text:
            return True
        if hasattr(self, "file_id") and self.file_id:
            return True
        if hasattr(self, "file_url") and self.file_url:
            return True
        if hasattr(self, "file_path") and self.file_path:
            return True
        if hasattr(self, "fwd_msg_no") and self.fwd_msg_no:
            return True
        if hasattr(self, "top_message") and self.top_message:
            return self.top_message.is_not_empty()
        if hasattr(self, "media") and self.media:
            return True
        return False

    __nonzero__ = is_not_empty  # if Message
    __str__ = toString  # user output
    __repr__ = toString  # debug output

    def __init__(self, receiver=None, reply_id=DEFAULT_MESSAGE_ID, reply_markup=None, disable_notification=False):
        """

        :param receiver:
        :param reply_id:
        :type  reply_id: int
        :param reply_markup:
        :param disable_notification:
        """
        self.args = []
        self.receiver = receiver
        self.reply_id = reply_id
        self.reply_markup = reply_markup
        self.disable_notification = disable_notification
        self._next_msg = None

    def get_args(self, receiver, reply_id) -> list:
        if not self.receiver:
            self.receiver = receiver
        if self.reply_id is DEFAULT_MESSAGE_ID:
            self.reply_id = reply_id
        return []
    # end def

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        raise NotImplementedError("Overwrite this function.")
    # end def
# end class


class MessageWithReplies(Message):
    """ makes it possible to reply to not yet sent messages """

    def __init__(self, top_message, *reply_messages):
        """
        Sends the top message first, and the reply_messages afterwards.
        # If a reply message is a list, it will converted to a new :class:`MessageWithReplies` object, with the first element being the reply top.

        :param top_message: The parent message
        :param reply_messages:
        """
        super().__init__()
        assert isinstance(top_message, Message)
        self.top_message = top_message
        assert isinstance(reply_messages, (list, tuple))
        if isinstance(reply_messages, tuple):
            reply_messages = list(reply_messages)
        # end if
        self.reply_messages = []
        assert isinstance(reply_messages, list)
        for i, other_msg in enumerate(reply_messages):
            if isinstance(other_msg, (list, tuple)):
                reply_messages.extend(other_msg)
                continue  # because we processed this element.
            try:  # just to add logging
                assert isinstance(other_msg, Message)
                self.reply_messages.append(other_msg)
            except AssertionError:
                logger.exception("reply_messages[{num}] is not type Message. Instead is {type}. Value is {value}.".format(
                    num=i, type=type(other_msg), value=other_msg
                ))
                raise
                # end try
        # end for
    # end def __init__

    @classmethod
    def from_list(cls, list_or_tuple):
        """
        `list[A, B, C]` -> `Message(A)` with reply-children `[B, C]`

        :param list_or_tuple:
        :return:
        """
        assert_instance(list_or_tuple, (list, tuple))
        return MessageWithReplies(list_or_tuple[0], list_or_tuple[1:])
    # end def

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        """
        Sends a MessageWithReplies.
        First sends the `self.top_message`, and then the `self.reply_messages`

        Will return a list with all the results.

        :return: list of all results. `top_message` first, followed by the `reply_messages`.
        :rtype: list
        """
        assert isinstance(self.top_message, Message)
        self.top_message._apply_update_receiver(receiver=self.receiver, reply_id=self.reply_id)
        top_message_result = self.top_message.send(sender)
        assert_instance(top_message_result, PytgbotApiMessage)
        top_msg_reply_id = top_message_result.message_id
        # end if
        reply_messages = list(self.reply_messages)  # tuple -> list, just in case
        reply_results = [top_message_result, ]  # the results of the sending.
        for child_msg in reply_messages:
            if isinstance(child_msg, (list, tuple)):
                reply_messages.extend(child_msg)
                continue
            assert_instance(child_msg, Message)
            child_msg._apply_update_receiver(receiver=self.receiver, reply_id=top_msg_reply_id)
            result = child_msg.send(sender)
            reply_results.append(result)
        # end for
        return reply_results
    # end def
# end class MessageWithReplies


class TypingMessage(Message):
    TYPING = "typing"
    RECORD_VIDEO = "record_video"
    UPLOAD_VIDEO = "upload_video"
    RECORD_AUDIO = "record_audio"
    UPLOAD_AUDIO = "upload_audio"
    UPLOAD_PHOTO = "upload_photo"
    UPLOAD_DOCUMENT = "upload_document"
    SELECTING_GEO = "find_location"
    CANCEL = ""

    def __init__(self, receiver: int=None, status=TYPING, reply_markup=None):
        super().__init__(receiver=receiver)
        self.status = status
        assert status in [  # check if is a valid status
            TypingMessage.TYPING, TypingMessage.RECORD_VIDEO, TypingMessage.UPLOAD_VIDEO, TypingMessage.RECORD_AUDIO,
            TypingMessage.UPLOAD_AUDIO, TypingMessage.UPLOAD_PHOTO, TypingMessage.UPLOAD_DOCUMENT,
            TypingMessage.SELECTING_GEO, TypingMessage.CANCEL
        ]  # check if is a valid status
        self.receiver = receiver
    # end def __init__

    def send(self, sender: PytgbotApiBot)->bool:
        return sender.send_chat_action(self.receiver, self.status)
    # end def
# end class


class DocumentMessage(Message):
    def __init__(
        self, file_id=None, file_path=None, file_url=None, file_content=None, file_mime=None, file=None,
        thumb=None,
        caption=None, parse_mode=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID, reply_markup=None,
        disable_notification=False
    ):
        """
        - You can specify a `file_id` to re-send existing content, already on telegram's servers.
        - You can specify a `file_url` to download it. It will get mime and filename from there.
        - You can specify a `file_path` to load it from disk. It will get mime and filename from there.
        - You can specify a `file_content` and a `file_path`. It will use the mime from the content, and get the filename part from the path.
        - You can specify a `file_content` and a `file_url`.  It will use the mime from the content, and get the filename part from the url.
        - You can specify a `file_content`, the `file_mime` and a `file_path`. It will use the mime from as in `file_mime`, and get the filename part from the path.
        - You can specify a `file_content`, the `file_mime` and a `file_url`.  It will use the mime from as in `file_mime`, and get the filename part from the url.
        - You can specify a `file` to provide an prepared :class:`InputFile` instance.



        :param file_id:
        :type  file_id: str|None

        :param file_path:
        :type  file_path: str|None

        :param file_url:
        :type  file_url: str|None

        :param file_content:
        :type  file_content: bytes|None

        :param caption:
        :type  caption: str|None

        :param parse_mode:
        :type  parse_mode: str|None

        :param receiver:
        :param reply_id:
        :param reply_markup:
        :param disable_notification:
        """
        super().__init__(receiver=receiver, reply_id=reply_id)
        assert_type_or_raise(file, None, InputFile, parameter_name='file')
        assert_type_or_raise(file_id, None, str, parameter_name='file_id')
        assert_type_or_raise(file_url, None, str, parameter_name='file_url')
        if not file_id and not file:
            if not file_path and not file_url and not file_content:
                raise AttributeError("Neither URL (file_url) nor local path (file_path) nor any binary data (file_content) given.")
            if file_path and not file_content and not file_url and not os.path.isfile(file_path):
                raise FileNotFoundError("There is no file '{path}', and there is no url or content given.".format(
                    path=self.file_path
                ))
            if file_content and file_path:
                logger.info("Binary data (file_content) given, using local path (file_path) for the name.")
            elif file_content and file_url:
                logger.info("Binary data (file_content) given, using url parameter (file_url) for the name.")
            elif not file_content and file_path and file_url:
                logger.info("File path (file_path) given, ignoring url parameter (file_url).")
                # logger.info("Both URL (file_url) AND a local path (file_path) given, using the file, if exists.")
                # THINKABOUT: try to use the file, and if it does not exist, download freshly. Like caching.
            # end if
        # end if
        self.file_input = file
        self.file_id = file_id
        self.file_content = file_content
        self.file_path = file_path
        self.file_url = file_url
        self.file_mime = file_mime if file_mime else None  # so any empty string will be None again.

        # prepare the files for upload
        self.prepare_file()

        # and the rest of the metadata
        self.caption=caption
        self.parse_mode=parse_mode
        self.reply_markup = reply_markup
        self.disable_notification = disable_notification
    # end def __init__

    def prepare_file(self):
        """
        This sets `self.file` to a fitting :class:`InputFile`
        or a fitting sublcass (:class:`InputFileFromDisk`, :class:`InputFileFromURL`)
        :return: Nothing
        """
        if self.file_input:
            self.file = self.file_input
        elif self.file_id:
            self.file = self.file_id
        elif self.file_content:
            file_name = "file"
            file_suffix = ".blob"
            if self.file_path:
                file_name = os.path.basename(os.path.normpath(self.file_path))  # http://stackoverflow.com/a/3925147
                file_name, file_suffix = os.path.splitext(file_name)  # http://stackoverflow.com/a/541394/3423324
            elif self.file_url:
                # http://stackoverflow.com/a/18727481/3423324#how-to-extract-a-filename-from-a-url-append-a-word-to-it
                url = urlparse(self.file_url)
                file_name = os.path.basename(url.path)
                file_name, file_suffix = os.path.splitext(file_name)
            # end if
            if self.file_mime:
                file_suffix = mimetypes.guess_extension(self.file_mime)
                file_suffix = '.jpg' if file_suffix == '.jpe' else file_suffix  # .jpe -> .jpg
            # end if
            if not file_suffix or not file_suffix.strip().lstrip("."):
                logger.debug("file_suffix was empty. Using '.blob'")
                file_suffix = ".blob"
            # end if
            file_name = "{filename}{suffix}".format(filename=file_name, suffix=file_suffix)
            self.file = InputFileFromBlob(self.file_content, file_name=file_name, file_mime=self.file_mime)
        elif self.file_path:
            self.file = InputFileFromDisk(self.file_path, file_mime=self.file_mime)
        elif self.file_url:
            self.file = InputFileFromURL(self.file_url, file_mime=self.file_mime)
        # end if
    # end def prepare_file

    def prepare_file(self):
        """
        This sets `self.file` to a fitting :class:`InputFile`
        or a fitting sublcass (:class:`InputFileFromDisk`, :class:`InputFileFromURL`)
        :return: Nothing
        """
        if self.file_input:
            self.file = self.file_input
        elif self.file_id:
            self.file = self.file_id
        elif self.file_content:
            file_name = "file"
            file_suffix = ".blob"
            if self.file_path:
                file_name = os.path.basename(os.path.normpath(self.file_path))  # http://stackoverflow.com/a/3925147
                file_name, file_suffix = os.path.splitext(file_name)  # http://stackoverflow.com/a/541394/3423324
            elif self.file_url:
                from urllib.parse import urlparse  # http://stackoverflow.com/a/18727481/3423324
                url = urlparse(self.file_url)
                file_name = os.path.basename(url.path)
                file_name, file_suffix = os.path.splitext(file_name)
            # end if
            if self.file_mime:
                import mimetypes
                file_suffix = mimetypes.guess_extension(self.file_mime)
                file_suffix = '.jpg' if file_suffix == '.jpe' else file_suffix  # .jpe -> .jpg
            # end if
            if not file_suffix or not file_suffix.strip().lstrip("."):
                logger.debug("file_suffix was empty. Using '.blob'")
                file_suffix = ".blob"
            # end if
            file_name = "{filename}{suffix}".format(filename=file_name, suffix=file_suffix)
            self.file = InputFileFromBlob(self.file_content, file_name=file_name, file_mime=self.file_mime)
        elif self.file_path:
            self.file = InputFileFromDisk(self.file_path, file_mime=self.file_mime)
        elif self.file_url:
            self.file = InputFileFromURL(self.file_url, file_mime=self.file_mime)
        # end if
    # end def prepare_file

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        self.prepare_file()
        try:
            return self.actual_sending(sender, ignore_reply=False)
        except TgApiServerException as e:
            if e.error_code == 400 and e.description.lower().startswith('bad request') and 'reply message not found' in e.description:
                logger.debug('Retry sending without `reply_to_message_id`.')
                return self.actual_sending(sender, ignore_reply=True)
            # end if
            raise  # else it just raises as usual
        # end try
    # end def send

    def actual_sending(self, sender: PytgbotApiBot, ignore_reply: bool = False) -> PytgbotApiMessage:
        assert_type_or_raise(self.reply_id, int, None, parameter_name="self.reply_id")  # not DEFAULT_MESSAGE_ID
        return sender.send_document(
            chat_id=self.receiver, document=self.file,
            caption=self.caption, parse_mode=self.parse_mode,
            reply_to_message_id=self.reply_id if not ignore_reply else None,
            reply_markup=self.reply_markup,
            disable_notification=self.disable_notification,
            allow_sending_without_reply=True,
        )
    # end def
# end class


class PhotoMessage(DocumentMessage):
    """
    Sends a photo, compressed.
    Use `ImageMessage` if you want to automaticly detect mime-type to send uncompressed if needed. (e.g. for gifs)
    """
    def __init__(self, file_id=None, file_path=None, file_url=None, file_content=None, file_mime=None, caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False):
        super().__init__(
            file_id=file_id, file_path=file_path, file_url=file_url, file_content=file_content, file_mime=file_mime, caption=caption,
            receiver=receiver, reply_id=reply_id, reply_markup=reply_markup, disable_notification=disable_notification
        )  # let DocumentMessage handle this
        if caption is not None and len(caption) > 140:
            logger.warning("Caption longer as 140. Cutting {len} characters.".format(len=len(caption) - 137))
            caption = cut_paragraphs(caption, length=140)[:140]
        self.caption = caption

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        self.prepare_file()
        assert isinstance(self.file, (InputFile, InputFileFromDisk, InputFileFromURL, str))
        if not self.file_id and not any([self.file.file_name.endswith(x) for x in [".jpg", ".jpeg", ".gif", ".png", ".tif", ".bmp"]]):
            # set the suffix
            if self.file.file_mime in ["image/jpg", "image/jpeg", "image/jpe"]:  # manually, to avoid .jpe ending.
                self.file.file_name += ".jpg"
            else:
                import mimetypes
                ext = mimetypes.guess_extension(self.file.file_mime)  # automatically
                if ext not in [".jpg", ".jpeg", ".gif", ".png", ".tif", ".bmp"]:
                    ext = ".unknown-file-type.png"  # At least we can try setting it as .png
                self.file.file_name += ext
            # end if
        # end if
        try:
            return sender.send_photo(
                chat_id=self.receiver, photo=self.file,
                caption=self.caption, reply_to_message_id=self.reply_id, reply_markup=self.reply_markup,
                disable_notification = self.disable_notification
            )
        except TgApiServerException as e:
            if e.error_code == 400 and e.description.startswith('bad request') and 'reply message not found' in e.description:
                logger.debug('Trying to resend without reply_to.')
                return sender.send_photo(
                    chat_id=self.receiver, photo=self.file,
                    caption=self.caption, reply_to_message_id=self.reply_id, reply_markup=self.reply_markup,
                    disable_notification=self.disable_notification
                )
            # end if
            raise  # else it just raises as usual
        # end try
    # end def send
# end class PhotoMessage


class StickerMessage(DocumentMessage):
    def __init__(self, file_id=None, file_path=None, file_url=None, file_content=None, file_mime=None, caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False):
        """
        :param file_id: the ID of the file
        :param receiver:
        :param reply_id:
        :param reply_markup:
        :param disable_notification:
        """
        super().__init__(
            file_id, caption=None, receiver=receiver, reply_id=reply_id, reply_markup=reply_markup,
            disable_notification=disable_notification
        )
    # end def __init__

    def actual_sending(self, sender: PytgbotApiBot, ignore_reply: bool = False) -> PytgbotApiMessage:
        return sender.send_sticker(
            chat_id=self.receiver, sticker=self.file_id,
            reply_to_message_id=self.reply_id if not ignore_reply else None,
            disable_notification=self.disable_notification
        )
    # end def
# end class


class MediaGroupMessage(Message):
    def __init__(self, media, receiver=None, reply_id=DEFAULT_MESSAGE_ID, reply_markup=None, disable_notification=False):
        """
        :param media: A array describing photos and videos to be sent, must include 2–10 items
        :type  media: list of (InputMediaPhoto|InputMediaVideo)

        Optional keyword parameters:

        :param receiver: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type  receiver: int | str|unicode

        :param disable_notification: Sends the messages silently. Users will receive a notification with no sound.
        :type  disable_notification: bool

        :param reply_id: If the messages are a reply, ID of the original message
        :type  reply_id: int
        """
        for i, medium in enumerate(media):
            assert_instance(medium, InputMediaPhoto, InputMediaVideo, parameter_name="media[{i}]".format(i=i))
        # end for
        self.media = media
        super(MediaGroupMessage, self).__init__(receiver, reply_id, reply_markup, disable_notification)
    # end def

    def is_not_empty(self):
        return self.media and len(self.media) > 2
    # end if

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        """
        :rtype: PytgbotApiMessage
        """
        return sender.send_media_group(
            chat_id=self.receiver, media=self.media,
            disable_notification=self.disable_notification, reply_to_message_id=self.reply_id
        )
    # end def
# end def


def ImageMessage(file_path=None, file_url=None, file_content=None, caption=None, receiver=None,
                 reply_id=DEFAULT_MESSAGE_ID, disable_notification=False):
    """
    If you want to automaticly detect mime-type to send uncompressed if needed. (e.g. for gifs)
    You could use `PhotoMessage` if you only do send png's and jpg's,
    or `DocumentMessage` to always send umcompressed.
    """
    mime = None
    # Getting MIME type
    if file_url:
        file = requests.get(file_url)
        file_content = file.content
        mime = magic.from_buffer(file_content, mime=True)
        logger.debug("Got mime type of url {url!r}: {mime}".format(url=file_url, mime=mime))
    elif file_path:
        mime = get_file_mime(file_path)
        logger.debug("Got mime type of file {path!r}: {mime}".format(path=file_path, mime=mime))
    elif file_content:
         mime = magic.from_buffer(file_content, True)
         logger.debug("Got mime type of the blob: {mime}".format(mime=mime))
    else:
        raise ValueError("Neither file_path, file_url nor file_content were given.")
    # end if
    if not mime:
        raise ValueError("Could not determaine file mime type.")
    # end if

    # select image type
    if mime in ["image/jpeg", "image/jpg", "image/png"]:
        return PhotoMessage(
            file_path=file_path, file_url=file_url, file_content=file_content, file_mime=mime, receiver=receiver, reply_id=reply_id,
            disable_notification=disable_notification, caption=caption
        )
    else:  # gif etc.
        doc = DocumentMessage(
            file_path=file_path, file_url=file_url, file_content=file_content, file_mime=mime, caption=caption, receiver=receiver, reply_id=reply_id,
            disable_notification=disable_notification
        )
        return doc
# end class


@deprecated('Use DocumentMessage instead.')
def FileIDMessage(*args, **kwargs):
    return DocumentMessage(*args, **kwargs)  # this probably fails.
# end def


class AudioMessage(DocumentMessage):
    """
    send an audio file
    """
    def __init__(
        self, file_id=None, file_path=None, file_url=None, file_content=None, file_mime=None,
        caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID, reply_markup=None, disable_notification=False
    ):
        """
        :param file_id: the ID of the file
        :param receiver:
        :param reply_id:
        :param reply_markup:
        :param disable_notification:
        """
        super().__init__(
            file_id=file_id, file_path=file_path, file_url=file_url, file_content=file_content, file_mime=file_mime,
            caption=caption,
            receiver=receiver, reply_id=reply_id, reply_markup=reply_markup, disable_notification=disable_notification
        )  # let DocumentMessage handle this
    # end def __init__

    def actual_sending(self, sender: PytgbotApiBot, ignore_reply: bool = False):
        return sender.send_audio(
            chat_id=self.receiver, audio=self.file_id,
            reply_to_message_id=self.reply_id if not ignore_reply else None,
            caption=self.caption, parse_mode=self.parse_mode,
            reply_markup=self.reply_markup, disable_notification=self.disable_notification
        )
    # end def
# end class


class GameMessage(Message):
    def __init__(self, game_short_name, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False):
        """
        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via Botfather.
        :type  game_short_name: str|unicode

        :param receiver:
        :param reply_id:
        :param reply_markup:
        :param disable_notification:
        """
        assert_instance(game_short_name, unicode_type, parameter_name="game_short_name")
        self.game_short_name = game_short_name
        super().__init__(
            receiver=receiver, reply_id=reply_id, reply_markup=reply_markup, disable_notification=disable_notification
        )
    # end def __init__

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        """
        :param sender: The default value
        :param receiver: The default value
        :param reply_id: The default value
        :return:
        """
        try:
            return sender.send_game(
                chat_id=self.receiver, game_short_name=self.game_short_name,
                disable_notification=self.disable_notification,
                reply_to_message_id=self.reply_id, reply_markup=self.reply_markup
            )
        except TgApiServerException as e:
            raise  # else it just raises as usual
        # end try
    # end def send
# end class


class ForwardMessage(Message):
    def __init__(self, msg_id, from_chat_id, receiver: int=None, reply_id=DEFAULT_MESSAGE_ID):
        super().__init__(receiver=receiver, reply_id=reply_id)
        if not isinstance(msg_id, int):
            raise ValueError("Message id is no integer.")
        self.msg_id = msg_id
        if not isinstance(from_chat_id, int):
            raise ValueError("Chat id is no integer.")
        self.from_chat_id = from_chat_id

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        try:
            return sender.forward_message(
                chat_id=self.receiver, from_chat_id=self.from_chat_id,
                message_id=self.msg_id, disable_notification=self.disable_notification
            )
        except TgApiServerException as e:
            raise  # else it just raises as usual
        # end try
    # end def send
# end class


PARSE_MODE_TEXT = "text"
PARSE_MODE_HTML = "html"
PARSE_MODE_MARKDOWN = "markdown"


class TextMessage(Message):
    class DEFAULT_MARKDOWN_IS_NONE(object): pass

    @caller
    def __init__(self, text, receiver=None, reply_id=DEFAULT_MESSAGE_ID, parse_mode=DEFAULT_MARKDOWN_IS_NONE, reply_markup=None,
                 disable_notification=False, disable_web_page_preview=True, call=None):
        super().__init__(receiver=receiver, reply_id=reply_id, reply_markup=reply_markup,
                         disable_notification=disable_notification)
        if parse_mode is TextMessage.DEFAULT_MARKDOWN_IS_NONE:
            if call:
                call = DictObject.objectify(call)
                logger.warning("No parse mode was set, do you need the old default 'markdown'?\n"
                               "Called from function {caller.name} at file {caller.file}:{caller.line}\n"
                               "The line is:\n"
                               "{caller.code}".format(**call)
                )
            else:
                logger.warning("No parse mode was set, do you need the old default 'markdown'?\nCaller unknown.")
            # end if
            parse_mode = "text"
        # end if
        if parse_mode == "text":
            parse_mode = None  # because "text" does not exist on TG Api.
        # end if
        texts = text_split(text, MAX_TEXT_LENGTH, max_parts=2)
        if len(texts) == 0:
            raise ValueError("Text was empty")
        if len(texts) == 1:
            logger.debug("Message has length {all} ({all_bytes} bytes). Not split.".format(
                all=len(text), all_bytes=len(escape(text).encode("utf-8"))
            ))
        else:
            logger.debug(
                "Message of length {all} ({all_bytes} bytes) split into {part} ({part_bytes} bytes) + {rest} more.".format(
                    all=len(text), all_bytes=len(escape(text).encode("utf-8")),
                    part=len(texts[0]), part_bytes=len(escape(texts[0]).encode("utf-8")), rest=len(texts) - 1
                )
            )
        # end if
        self.disable_web_page_preview = disable_web_page_preview
        self.parse_mode = parse_mode
        self.text = texts[0]
        if len(texts) > 1:
            self.receiver = receiver
            self._next_msg = TextMessage(
                texts[1], receiver=receiver, parse_mode=self.parse_mode, reply_markup=reply_markup,
                disable_notification=disable_notification
            )
        # end if
        if not text:
            raise ValueError("No text provided.")
        # end if
    # end def __init__

    def send(self, sender: PytgbotApiBot) -> PytgbotApiMessage:
        try:
            result = sender.send_message(
                chat_id=self.receiver, text=self.text,
                parse_mode=self.parse_mode, disable_notification=self.disable_notification,
                reply_to_message_id=self.reply_id, reply_markup=self.reply_markup,
                disable_web_page_preview=self.disable_web_page_preview,
                allow_sending_without_reply=True,
            )
        except TgApiServerException as e:
            raise  # else it just raises as usual
        # end try

        # if result and self._next_msg:
        #     # pass current message as reply id.
        #     self._next_msg.reply_id == result
        # # end if
        return result
    # end def
# end class


class PlainMessage(TextMessage):
    """
    Subclass of :class:`TextMessage`, with the type set to "text".
    """
    def __init__(self, text, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False, disable_web_page_preview=True):
        super().__init__(text, receiver, reply_id, PARSE_MODE_TEXT, reply_markup, disable_notification,
                         disable_web_page_preview)
    # end def
# end class


class HTMLMessage(TextMessage):
    """
    Subclass of :class:`TextMessage`, with the type set to "html".
    """
    def __init__(self, text, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False, disable_web_page_preview=True):
        super().__init__(text, receiver, reply_id, PARSE_MODE_HTML, reply_markup, disable_notification,
                         disable_web_page_preview)
    # end def
# end class


class MarkdownMessage(TextMessage):
    """
    Subclass of :class:`TextMessage`, with the type set to "markdown".
    """
    def __init__(self, text, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False, disable_web_page_preview=True):
        super().__init__(text, receiver, reply_id, PARSE_MODE_MARKDOWN, reply_markup, disable_notification,
                         disable_web_page_preview)
    # end def
# end class


def escape_markdown(input_string, strip=False):
    """
    Escapes markdown tags, so text is safe for telegram.
    "lol_wat" -> "lol\_wat"
     Funfact, Telegram is parsing markdown so poorly, you should probably use html instead.

    :param input_string:
    :return:
    """
    result = ""
    escaped = False
    if strip:
        for character in input_string:
            if character == "\\":
                escaped = True
                continue
            elif character in ["_", "*", "`"]:
                if escaped:
                    result = result[:-1]
                    escaped = False
                    continue
                # end if
            # end if
            escaped = False
            result += character
        # end for
        return result
    # end if

    code = False
    for character in input_string:
        if character == "\\":
            escaped = True
        elif character == "`":
            if not escaped:
                code = not code
            # end if
            result += character
        elif character in ["_", "*"]:
            if escaped:
                result += character
            else:
                result += "\\" + character
                escaped = False
                # end if
        else:
            result += character
            # end if
    # end for
    return result
# end def


def style_exclude_users(input_string, start_style="_", end_style=None):
    """
    Escapes markdown tags, so text is safe for telegram.
    "@luckydonald hits @someone with a fork" -> "@luckydonald _hits_ @someone _with a fork_"


    >>> style_exclude_users("@username hits @example")
    '@username _hits_ @example'

    >>> style_exclude_users("Some @username hits @example")
    '_Some_ @username _hits_ @example'

    >>> style_exclude_users("Some @username hits @example fast.")
    '_Some_ @username _hits_ @example _fast._'

    >>> style_exclude_users("@username")
    '@username'

    >>> style_exclude_users("@rarity was _really_ generous today!")
    '@rarity _was really generous today!_'

    >>> style_exclude_users("@littlepip is *best* pony!")
    '@littlepip _is *best* pony!_'

    :param input_string:
    :return:
    """
    if end_style is None:
        end_style = start_style[::-1]  # reverse it
    # end if
    assert isinstance(start_style, str)
    assert isinstance(end_style, str)

    def wrap_hit_in_style(matchobj):
        # print(matchobj)
        return start_style + matchobj.group(0) + end_style

    # end def
    input_string = start_style + re.sub(pattern=RE_TG_USERNAME, repl=wrap_hit_in_style,
                                        string=input_string.replace(start_style, "").replace(end_style, "")) + end_style
    if input_string.startswith(start_style * 2):
        input_string = input_string[len(start_style) * 2:]
    # end if
    if input_string.endswith(end_style * 2):
        input_string = input_string[:-len(end_style) * 2]
    # end if
    return input_string
# end def
