# coding: utf8
import logging
import os.path

from dingtalkchatbot.chatbot import DingtalkChatbot, CardItem
import feedparser
import yaml


class RSSBot(object):
    def __init__(self):
        dingToken = os.environ.get("DD_TOKEN").strip()
        dingSecret = os.environ.get("DD_SECRET").strip()
        self._caches = self._loadYaml("caches.yaml")
        self._subscrites = self._loadYaml("subscrites.yaml")
        webhook = "https://oapi.dingtalk.com/robot/send?access_token=" + dingToken
        self._cardItems = []
        self._chatbot = DingtalkChatbot(webhook=webhook, secret=dingSecret)

    @staticmethod
    def _loadYaml(yamlFile):
        filepath = os.path.dirname(__file__) + os.sep + yamlFile
        fp = open(filepath)
        contents = yaml.load(fp, Loader=yaml.FullLoader)
        return contents

    def _writeCaches(self):
        yamlFile = os.path.dirname(__file__) + os.sep + "caches.yaml"
        wp = open(yamlFile, 'w')
        yaml.dump(self._caches, wp)

    def _pushMessage(self, feedMeta, feedEntries):
        cards = []
        picUrl = "https://images.unsplash.com/photo-1548092372-0d1bd40894a3?ixid=" \
                 "MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&ixlib=rb-1.2.1&auto=format&fit=crop&w=400&q=80"
        for entry in feedEntries:
            cardItem = CardItem(title=entry.title + " - " + feedMeta.title, url=entry.link, pic_url=picUrl)
            cards.append(cardItem)
        self._chatbot.send_feed_card(cards)

    def parseFeed(self, url):
        try:
            feed = feedparser.parse(url)
            feedCache = self._caches["cache"].get(url, None)
            cache = {
                "latest_id": str(feed.entries[0]["id"])
            }
            if not feedCache:
                self._caches["cache"][url] = cache
                self._writeCaches()
                return feed
            if feedCache["latest_id"] != cache["latest_id"]:
                # 生成新的 entries替换 feed.entries
                lastID = len(feed.entries)
                for e in feed.entries:
                    if e.id == feedCache["latest_id"]:
                        lastID = feed.entries.index(e)
                        break
                newEntries = feed.entries[:lastID]
                feed.entries = newEntries
                self._caches["cache"][url] = cache
                self._writeCaches()
                return feed
            else:
                return None
        except Exception as err:
            logging.error("{0} exception: {1}".format(url, err))
            return None

    def getNewFeed(self):
        for url in self._subscrites["subscrites"]:
            feed = self.parseFeed(url)
            if not feed:
                continue
            self._pushMessage(feed.feed, feed.entries)


if __name__ == '__main__':
    bot = RSSBot()
    bot.getNewFeed()
