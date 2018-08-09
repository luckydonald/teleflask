import unittest
from unittest.mock import Mock
from pytgbot.api_types.sendable.files import InputFileFromURL
from pytgbot.api_types.sendable.input_media import InputMediaPhoto, InputMediaVideo

from teleflask.messages import MediaGroupMessage


class Bot(object):
    pass

class MessagesTestCase(unittest.TestCase):
    def test_media_group(self):

        b = Bot()
        b.send_media_group = Mock()
        url1 = 'https://derpicdn.net/img/view/2012/1/22/1382.jpg'
        # url2 = 'https://derpicdn.net/img/view/2016/2/3/1079240.png'
        vid1 = 'https://derpicdn.net/img/view/2016/12/21/1322277.mp4'
        pic1 = 'https://derpicdn.net/img/2017/7/21/1491832/thumb.jpeg'

        media = [
            InputMediaPhoto(url1, caption='1'),
            InputMediaPhoto(InputFileFromURL(url1), caption='2'),
            InputMediaVideo(vid1, caption='3'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=pic1, caption='4'),
            InputMediaVideo(InputFileFromURL(vid1), thumb=InputFileFromURL(pic1), caption='5'),
        ]

        m = MediaGroupMessage(media, disable_notification=True)

        receiver = 123
        reply_id = 532
        m.send(b, receiver, reply_id)
        b.send_media_group.assert_called_once_with(
            receiver, media, disable_notification=True, reply_to_message_id=reply_id
        )
    # end def


if __name__ == '__main__':
    unittest.main()
# end if
