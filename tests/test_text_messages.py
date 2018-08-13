import unittest

from teleflask.messages import HTMLMessage


class SenderMockup(object):
    def __init__(self):
        self.args = None
        self.kwargs = None
    # end def

    def _send_proxy(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    # end def

    def __getattr__(self, item):
        print("Proxying function \"{f}\"".format(f=item))
        if item.startswith("send_"):
            return self._send_proxy
        # end if
        return super().__getattribute__(item)
    # end def
# end class


s = SenderMockup()
s.send_("test")


class SomeUpdatesMixinTestCase(unittest.TestCase):
    _TEXT = "test text"
    _RECEIVER = "@username"

    def setUp(self):
        self.s = SenderMockup()
    # end def

    def test_html_message(self):
        m = HTMLMessage(self._TEXT, self._RECEIVER)
        with self.subTest():
            self._test_message_basics(m)
        # end with
        m.send(self.s, "RECEIVER", None)
        self.assertTupleEqual(self.s.args, ('@username', 'test text'), "args")
        self.assertDictEqual(self.s.kwargs, {'parse_mode': 'html', 'disable_notification': False, 'reply_to_message_id': None, 'reply_markup': None, 'disable_web_page_preview': True}, "args")
    # end def

    def _test_message_basics(self, m):
        self.assertEqual(m.text, self._TEXT, ".text")
        self.assertEqual(m.receiver, self._RECEIVER, ".receiver")
    # end def
# end class


if __name__ == "__main__":
    unittest.main()
# end if
