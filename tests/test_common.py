from pyircbot import common


def test_parse_line():
    assert common.parse_irc_line(":chuck!~chuck@foobar PRIVMSG #jesusandhacking :asdf") == \
        ('PRIVMSG', ['#jesusandhacking'], 'chuck!~chuck@foobar', "asdf")


def test_parse_notrailing():
    assert common.parse_irc_line(":chuck!~chuck@foobar MODE #jesusandhacking -o asciibot") == \
        ('MODE', ['#jesusandhacking', '-o', 'asciibot'], 'chuck!~chuck@foobar', None)
