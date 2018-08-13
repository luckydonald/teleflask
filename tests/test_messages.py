import unittest
from pytgbot.api_types.receivable.media import PhotoSize
from pytgbot.exceptions import TgApiServerException
from unittest.mock import Mock, ANY
from pytgbot.api_types.sendable.files import InputFileFromURL
from pytgbot.api_types.sendable.input_media import InputMediaPhoto, InputMediaVideo
from pytgbot.bot import Bot as APIBot
from luckydonaldUtils.logger import logging

from somewhere import API_KEY, TEST_CHAT
from teleflask.messages import MediaGroupMessage, PhotoMessage, FileIDMessage


__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class Bot(object):
    pass
# end class


pic1 = 'https://derpicdn.net/img/view/2012/1/22/1382.jpg'
pic2 = 'https://derpicdn.net/img/view/2016/2/3/1079240.png'
tmb1 = 'https://derpicdn.net/img/2017/7/21/1491832/thumb.jpeg'
vid1 = 'https://derpicdn.net/img/view/2016/12/21/1322277.mp4'


class MessagesTestCase(unittest.TestCase):
    def test_media_group(self):
        b = Bot()
        b.send_media_group = Mock()

        media = [
            InputMediaPhoto(pic1, caption='1'),
            InputMediaPhoto(InputFileFromURL(pic1), caption='2'),
            InputMediaVideo(vid1, caption='3'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=tmb1, caption='4'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=InputFileFromURL(tmb1), caption='5'),
        ]

        m = MediaGroupMessage(media, disable_notification=True)

        receiver = 123
        reply_id = 532
        m.send(b, receiver, reply_id)
        b.send_media_group.assert_called_once_with(
            receiver, media, disable_notification=True, reply_to_message_id=reply_id
        )
        self.assertTrue(True)
    # end def

    def test_photo_url(self):
        b = Bot()  # type: APIBot
        b.send_photo = Mock()

        m = PhotoMessage(file_url=pic1, disable_notification=True)

        receiver = 123
        reply_id = 532
        m.send(b, receiver, reply_id)
        b.send_photo.assert_called_once_with(
            receiver, ANY, disable_notification=True, reply_to_message_id=reply_id, caption=None, reply_markup=None
        )
        # check ANY:
        args, kwargs = b.send_photo.call_args
        self.assertIsInstance(args[1], InputFileFromURL)
        self.assertEqual(args[1].file_url, pic1)
    # end def

    def test_photo_file_id(self):
        b = Bot()  # type: APIBot
        b.send_photo = Mock()

        m = PhotoMessage(file_id='test4458file', disable_notification=True)

        receiver = 123
        reply_id = 532
        m.send(b, receiver, reply_id)
        b.send_photo.assert_called_once_with(
            receiver, ANY, disable_notification=True, reply_to_message_id=reply_id, caption=None, reply_markup=None
        )
        # check ANY:
        args, kwargs = b.send_photo.call_args
        self.assertIsInstance(args[1], str)
        self.assertEqual(args[1], 'test4458file')
    # end def
# end class


class MessageTypesRealSendingTest(unittest.TestCase):
    def setUp(self):
        self.bot = APIBot(API_KEY)
        self.messages = []
        self.messages.append(self.bot.send_message(TEST_CHAT, 'Unittest started.'))
        self.reply_to = self.messages[0].message_id
    # end def

    def test_send_media_group(self):
        media = [
            InputMediaPhoto(pic1, caption='1'),
            InputMediaPhoto(InputFileFromURL(pic1), caption='2'),
            InputMediaVideo(vid1, caption='3'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=tmb1, caption='4'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=InputFileFromURL(tmb1), caption='5'),
        ]
        msgs = self.bot.send_media_group(TEST_CHAT, media, disable_notification=True, )
        self.messages.extend(msgs)

        self.messages.append(self.bot.send_message(TEST_CHAT, 'done with unittest {}.'.format(self.id())))
    # end def

    def test_media_group(self):
        media = [
            InputMediaPhoto(pic1, caption='1'),
            InputMediaPhoto(InputFileFromURL(pic1), caption='2'),
            InputMediaVideo(vid1, caption='3'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=tmb1, caption='4'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=InputFileFromURL(tmb1), caption='5'),
        ]

        m = MediaGroupMessage(media, disable_notification=True)

        msg = m.send(self.bot, TEST_CHAT, self.reply_to)
        self.messages.extend(msg)
        self.messages.append(self.bot.send_message(TEST_CHAT, 'done with unittest {}.'.format(self.id())))
    # end def

    def test_photo_url(self):
        m = PhotoMessage(file_url=pic1, disable_notification=True)

        msg = m.send(self.bot, TEST_CHAT, self.reply_to)
        self.assertIsNotNone(msg)
        self.messages.append(msg)
        self.messages.append(self.bot.send_message(TEST_CHAT, 'done with unittest {}.'.format(self.id())))
    # end def

    def test_photo_file_id(self):
        photo_msg = self.bot.send_photo(TEST_CHAT, photo=pic2, caption='this has a file_id')
        self.messages.append(photo_msg)
        file_id = self._get_biggest_photo_fileid(photo_msg)

        m = PhotoMessage(file_id=file_id, disable_notification=True)

        msg = m.send(self.bot, TEST_CHAT, self.reply_to)
        self.assertIsNotNone(msg)
        self.messages.append(msg)
        self.messages.append(self.bot.send_message(TEST_CHAT, 'done with unittest {}.'.format(self.id())))
    # end def

    #
    # utils:
    #

    def _get_biggest_photo_fileid(self, msg):
        biggest = msg.photo[0]
        for photo in msg.photo:
            self.assertIsInstance(photo, PhotoSize)
            if photo.file_size > biggest.file_size:
                biggest = photo
            # end if
        # end for
        return biggest.file_id
    # end def

    def tearDown(self):
        if self.bot and self.messages:
            for msg in reversed(self.messages):
                try:
                    self.bot.delete_message(TEST_CHAT, msg.message_id)
                except TgApiServerException as e:
                    if e.error_code == 400 and e.description == 'Bad Request: message to delete not found':
                        logger.info('delete message fail, not found.')
                        continue
                    # end if
                    logger.debug('delete message fail.', exc_info=True)
                # end try
            # end for
        # end if
        self.messages = []
    # end def
# end class


if __name__ == '__main__':
    unittest.main()
# end if
