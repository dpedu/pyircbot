import pytest
from time import sleep
from unittest.mock import MagicMock
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def linkbot(fakebot):
    """
    Provide a bot loaded with the Calc module. Clear the database.
    """
    fakebot.botconfig["module_configs"]["LinkTitler"] = {
        "reddit": {
            "user_agent": "pyircbot3 by /u/(changeme)",
            "client_id": "test",
            "client_secret": "test",
            "username": "test",
            "password": "test"
        },
        "youtube_api_key": "test"
    }

    fakebot.loadmodule("LinkTitler")
    return fakebot


def test_link_html_title(linkbot, monkeypatch):
    monkeypatch.setattr(linkbot.moduleInstances["LinkTitler"], "url_headers", lambda url: {"Content-Type": "text/html"})
    monkeypatch.setattr(linkbot.moduleInstances["LinkTitler"], "url_htmltitle", lambda url: "foo bar title")
    linkbot.feed_line("http://example.com/")
    sleep(0.1)
    linkbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: \x02foo bar title\x02')


def test_youtube(linkbot, monkeypatch):
    monkeypatch.setattr(linkbot.moduleInstances["LinkTitler"], "_get_video_description_api",
                        lambda vid_id: {"kind": "youtube#videoListResponse", "etag": "\"xxxx\"", "pageInfo": {"totalResults": 1, "resultsPerPage": 1}, "items": [{"kind": "youtube#video", "etag": "\"xxxx\"", "id": "SvArQjKr488", "snippet": {"publishedAt": "2009-06-16T06:12:24.000Z", "channelId": "UCgeRcbMDaVTwEHJvO6-hFjQ", "title": "Liquid X - RIoT Rich", "description": "blah", "thumbnails": {"default": {"url": "https://i.ytimg.com/vi/SvArQjKr488/default.jpg", "width": 120, "height": 90}, "medium": {"url": "https://i.ytimg.com/vi/SvArQjKr488/mqdefault.jpg", "width": 320, "height": 180}, "high": {"url": "https://i.ytimg.com/vi/SvArQjKr488/hqdefault.jpg", "width": 480, "height": 360}}, "channelTitle": "Bieji", "tags": ["liquid", "riot", "rich", "digital", "gangster", "nerd", "life", "rit", "Rochester", "Institute", "of", "Technology"], "categoryId": "10", "liveBroadcastContent": "none", "localized": {"title": "Liquid X - RIoT Rich", "description": "blah"}}, "contentDetails": {"duration": "PT5M39S", "dimension": "2d", "definition": "sd", "caption": "false", "licensedContent": False, "projection": "rectangular"}, "statistics": {"viewCount": "17141", "likeCount": "193", "dislikeCount": "8", "favoriteCount": "0", "commentCount": "31"}}]})
    linkbot.feed_line("blah blah https://www.youtube.com/watch?v=SvArQjKr488 blah blah")
    sleep(0.1)
    linkbot.act_PRIVMSG.assert_called_once_with('#test', '\x02\x031,0You\x0f\x030,4Tube\x02\x0f :: \x02Liquid X - RIoT Rich\x02 - length \x025m 39s\x02 - rated \x024.80/5\x02 - \x0217,141\x02 views - by \x02Bieji\x02 on \x022009.06.16\x02')


def test_reddit(linkbot, monkeypatch):
    fake = MagicMock()
    fake.title = "TIL X11 forwarding is (basically) as simple as running 'ssh -X user@hostname'"
    fake.domain = "self.todayilearned"
    fake.ups = 6
    fake.upvote_ratio = 0.67
    fake.over_18 = False
    fake.num_comments = 6
    fake.author.name = "drfrogsplat"
    fake.created = 1260361210

    monkeypatch.setattr(linkbot.moduleInstances["LinkTitler"], "get_reddit_submission", lambda sub_id: fake)
    linkbot.feed_line("blah blah https://www.reddit.com/r/todayilearned/comments/acm26/til_x11_forwarding_is_basically_as_simple_as/ blah blah")
    sleep(0.1)
    linkbot.act_PRIVMSG.assert_called_once_with('#test', "👽 \x02\x031,15REDDIT\x0f\x02 :: TIL X11 forwarding is (basically) as simple as running 'ssh -X user@hostname' \x02on \x02self.todayilearned\x02 - points \x026\x02 (67%↑) - comments \x026\x02 -  by \x02drfrogsplat\x02 on \x022009.12.09\x02")

