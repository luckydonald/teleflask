# -*- coding: utf-8 -*-
import re
import os  # file existence check before upload.
import magic
import logging
import backoff
import requests

from DictObject import DictObject

from luckydonaldUtils.exceptions import assert_or_raise as assert_instance
from luckydonaldUtils.text import text_split, cut_paragraphs, escape
from luckydonaldUtils.files.mime import get_file_mime

from pytgbot import Bot as PytgbotApiBot
from pytgbot.api_types.receivable.updates import Message as PytgbotApiMessage
from pytgbot.api_types.sendable.files import InputFile, InputFileFromDisk, InputFileFromURL
from pytgbot.exceptions import TgApiServerException

__all__ = ["TypingMessage", "TextMessage", "DocumentMessage", "PhotoMessage", "ImageMessage", "ForwardMessage"]
__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 4096  # should be 2048?
RE_TG_USERNAME = "((^|\s*)@(?P<username>(?:[a-z](?:[a-z0-9]|_(?!_)){3,}[a-z0-9])|" \
                 "(?:gif|vid|wiki|pic|bing|imdb|bold))(\s*|$))"  # https://regex101.com/r/gS5lZ6/2


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


def should_backoff(e):
    """
    Checks if it should raise an DoRetryException.

    Used for backoff strategy
    """
    if e.error_code == 429 or "too many requests" in e.description or "retry later" in e.description:
        import re
        from time import sleep
        error_wait_match = re.compile("Too Many Requests: retry after (\d+)").match(e.description)
        if error_wait_match:
            seconds_to_wait = int(error_wait_match.group(1))
            logger.warn("API Error: Too many Telegram requests. Instructed to wait {many} seconds.".format(many=seconds_to_wait))
            if seconds_to_wait > 600:  # 10 Minutes
                seconds_to_wait = 600
                logger.warn("Maximum is waiting 600 seconds (10 minutes).")
            sleep(seconds_to_wait + 1)  # It always is one second more. Go figure
        raise DoRetryException()
    # end if
# end def


class Message(object):
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
        return False

    __nonzero__ = is_not_empty  # if Message
    __str__ = toString  # user output
    __repr__ = toString  # debug output

    def __init__(self, receiver=None, reply_id=DEFAULT_MESSAGE_ID, reply_markup=None, disable_notification=False):
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

    def send(self, sender: PytgbotApiBot, receiver, reply_id)->PytgbotApiMessage:
        raise NotImplementedError("Overwrite this function.")
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

    def send(self, sender: PytgbotApiBot, receiver, reply_id):
        top_message_result = self.top_message.send(sender, receiver=receiver, reply_id=reply_id)
        assert_instance(top_message_result, PytgbotApiMessage)
        reply_id = top_message_result.message_id
        # end if
        reply_messages = list(self.reply_messages)  # tuple -> list, just in case
        for child_msg in reply_messages:
            if isinstance(child_msg, (list, tuple)):
                reply_messages.extend(child_msg)
                continue
            assert_instance(child_msg, Message)
            child_msg.send(sender, receiver, reply_id)
        # end for
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
        assert status in [
            TypingMessage.TYPING, TypingMessage.RECORD_VIDEO, TypingMessage.UPLOAD_VIDEO, TypingMessage.RECORD_AUDIO,
            TypingMessage.UPLOAD_AUDIO, TypingMessage.UPLOAD_PHOTO, TypingMessage.UPLOAD_DOCUMENT,
            TypingMessage.SELECTING_GEO
        ]  # valid status
        self.receiver = receiver
    # end def __init__

    def send(self, sender: PytgbotApiBot, receiver, reply_id)->bool:
        if self.receiver:
            receiver = self.receiver
        # end if
        return sender.send_chat_action(receiver, self.status)
    # end def
# end class


class DocumentMessage(Message):

    def __init__(self, file_path=None, file_url=None, file_content=None, file_mime=None, caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False):
        """
        You can specify a `file_path` to load it from disk. It will get mime and filename from there.
        You can specify a `file_content` and a `file_path`. It will use the mime from the content, and get the filename part from the path.
        You can specify a `file_content` and a `file_url`.  It will use the mime from the content, and get the filename part from the url.


        :param file_path:
        :param file_url:
        :param file_content:
        :param caption:
        :param receiver:
        :param reply_id:
        :param reply_markup:
        :param disable_notification:
        """
        super().__init__(receiver=receiver, reply_id=reply_id)
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
        self.file_content = file_content
        self.file_path = file_path
        self.file_url = file_url
        self.file_mime = file_mime if file_mime else None  # so any empty string will be None again.

        # prepare the files for upload
        self.prepare_file()

        # and the rest of the metadata
        self.caption=caption
        self.reply_markup = reply_markup
        self.disable_notification = disable_notification
    # end def __init__


    def prepare_file(self):
        """
        This sets `self.file` to a fitting :class:`InputFile`
        or a fitting sublcass (:class:`InputFileFromDisk`, :class:`InputFileFromURL`)
        :return: Nothing
        """
        if self.file_content:
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
            elif self.file_mime:
                import mimetypes
                file_suffix = mimetypes.guess_extension("image/jpeg")
                file_suffix = '.jpg' if file_suffix == '.jpe' else file_suffix  # .jpe -> .jpg
            # end if
            if not file_suffix or not file_suffix.strip().lstrip("."):
                file_suffix = ".blob"
            # end if
            file_name = "{filename}{suffix}".format(filename=file_name, suffix=file_suffix)
            self.file = InputFile(self.file_content, file_name=file_name, file_mime=self.file_mime)
        elif self.file_path:
            self.file = InputFileFromDisk(self.file_path, file_mime=self.file_mime)
        elif self.file_url:
            self.file = InputFileFromURL(self.file_url, file_mime=self.file_mime)
        # end if
    # end def prepare_file


    @backoff.on_exception(backoff.expo, DoRetryException, max_tries=10, jitter=None)
    def send(self, sender: PytgbotApiBot, receiver, reply_id)->PytgbotApiMessage:
        if self.receiver:
            receiver = self.receiver
        # end if
        if self.reply_id is not DEFAULT_MESSAGE_ID:
            reply_id = self.reply_id
        # end if
        self.prepare_file()
        try:
            return sender.send_document(
                receiver, self.file, caption=self.caption, reply_to_message_id=reply_id, reply_markup=self.reply_markup,
                disable_notification=self.disable_notification
            )
        except TgApiServerException as e:
            should_backoff(e)  # checks if it should raise an DoRetryException
            raise  # else it just raises as usual
            # end try
            # end def send
# end class


class PhotoMessage(DocumentMessage):
    """
    Sends a photo, compressed.
    Use `ImageMessage` if you want to automaticly detect mime-type to send uncompressed if needed. (e.g. for gifs)
    """
    def __init__(self, file_path=None, file_url=None, file_content=None, file_mime=None, caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False):
        super().__init__(
            file_path, file_url=file_url, file_content=file_content, file_mime=file_mime, caption=caption,
            receiver=receiver, reply_id=reply_id, reply_markup=reply_markup, disable_notification=disable_notification
        )  # let DocumentMessage handle this
        if caption is not None and len(caption) > 140:
            logger.warn("Caption longer as 140. Cutting {len} characters.".format(len=len(caption) - 137))
            caption = cut_paragraphs(caption, length=140)[:140]
        self.caption = caption

    @backoff.on_exception(backoff.expo, DoRetryException, max_tries=20, jitter=None)
    def send(self, sender: PytgbotApiBot, receiver, reply_id)->PytgbotApiMessage:
        if self.receiver:
            receiver = self.receiver
        # end if
        if self.reply_id is not DEFAULT_MESSAGE_ID:
            reply_id = self.reply_id
        # end if
        self.prepare_file()
        assert isinstance(self.file, (InputFile, InputFileFromDisk, InputFileFromURL))
        if not any([self.file.file_name.endswith(x) for x in [".jpg", ".jpeg", ".gif", ".png", ".tif", ".bmp"]]):
            if self.file.file_mime in ["image/jpg", "image/jpeg", "image/jpe"]:  # manually, to avoid .jpe ending.
                self.file.file_name+=".jpg"
            else:
                import mimetypes
                ext = mimetypes.guess_extension(self.file.file_mime)  # automatically
                if ext not in [".jpg", ".jpeg", ".gif", ".png", ".tif", ".bmp"]:
                    ext = ".unknown-file-4458.png"  # At least we can try setting it as .png
                self.file.file_name += ext
        try:
            return sender.send_photo(
                receiver, self.file, caption=self.caption, reply_to_message_id=reply_id, reply_markup=self.reply_markup,
                disable_notification = self.disable_notification
            )
        except TgApiServerException as e:
            should_backoff(e)  # checks if it should raise an DoRetryException
            raise  # else it just raises as usual
        # end try
    # end def send
# end class PhotoMessage


def ImageMessage(file_path=None, file_url=None, file_content=None, caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 disable_notification=False):
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


class FileIDMessage(Message):
    def __init__(self, file_id, caption=None, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
                 reply_markup=None, disable_notification=False):
        """
        :param file_id: the ID of the file
        :param caption: A optional string.
        :param receiver:
        :param reply_id:
        :param reply_markup:
        :param disable_notification:
        """
        super().__init__(receiver=receiver, reply_id=reply_id, reply_markup=reply_markup,
                         disable_notification=disable_notification)
        self.file_id = file_id
        self.caption=caption
    # end def __init__

    @backoff.on_exception(backoff.expo, DoRetryException, max_tries=10, jitter=None)
    def send(self, sender: PytgbotApiBot, receiver, reply_id)->PytgbotApiMessage:
        if self.receiver:
            receiver = self.receiver
        # end if
        if self.reply_id is not DEFAULT_MESSAGE_ID:
            reply_id = self.reply_id
        # end if
        try:
            return self.actual_sending(sender, receiver, reply_id)
        except TgApiServerException as e:
            should_backoff(e)  # checks if it should raise an DoRetryException
            raise  # else it just raises as usual
        # end try
    # end def send

    def actual_sending(self, sender: PytgbotApiBot, receiver, reply_id):
        return sender.send_document(
            receiver, self.file_id, caption=self.caption, reply_to_message_id=reply_id,
            reply_markup=self.reply_markup, disable_notification=self.disable_notification
        )
    # end def
# end class


class StickerMessage(FileIDMessage):
    def __init__(self, file_id, receiver=None, reply_id=DEFAULT_MESSAGE_ID,
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

    def actual_sending(self, sender: PytgbotApiBot, receiver, reply_id):
        return sender.send_sticker(
            receiver, self.file_id, reply_to_message_id=reply_id,
            reply_markup=self.reply_markup, disable_notification=self.disable_notification
        )
    # end def
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

    @backoff.on_exception(backoff.expo, DoRetryException, max_tries=20, jitter=None)
    def send(self, sender: PytgbotApiBot, receiver, reply_id)->PytgbotApiMessage:
        if self.receiver:
            receiver = self.receiver
        # end if
        if self.reply_id is not DEFAULT_MESSAGE_ID:
            reply_id = self.reply_id
        # end if
        try:
            return sender.forward_message(
                receiver, self.from_chat_id, self.msg_id, disable_notification=self.disable_notification
            )
        except TgApiServerException as e:
            should_backoff(e)  # checks if it should raise an DoRetryException
            raise  # else it just raises as usual
        # end try
    # end def send
# end class



class TextMessage(Message):
    from luckydonaldUtils.functions import caller
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

    @backoff.on_exception(backoff.expo, DoRetryException, max_tries=20, jitter=None)
    def send(self, sender: PytgbotApiBot, receiver, reply_id)->PytgbotApiMessage:
        if self.receiver:
            receiver = self.receiver
        # end if
        if self.reply_id is not DEFAULT_MESSAGE_ID:
            reply_id = self.reply_id
        # end if
        try:
            result = sender.send_message(
                receiver, self.text, parse_mode=self.parse_mode, disable_notification=self.disable_notification,
                reply_to_message_id=reply_id, reply_markup=self.reply_markup,
                disable_web_page_preview=self.disable_web_page_preview
            )
        except TgApiServerException as e:
            should_backoff(e)  # checks if it should raise an DoRetryException
            raise  # else it just raises as usual
        # end try
        if result and self._next_msg:
            pass  # TODO pass current message as reply id.
            # self._next_msg.reply_id == result
        # end if
        return result
    # end def


def escape_markdown(input_string, strip=False):
    """
    Escapes markdown tags, so text is safe for telegram.
    "lol_wat" -> "lol\_wat"

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