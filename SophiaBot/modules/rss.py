from asyncio import get_event_loop, sleep
from feedparser import parse
from pyrogram import filters
from pyrogram.types import Message
from SophiaBot import RSS_DELAY, pbot as app
from SophiaBot.core.decorators.errors import capture_err
from SophiaBot.function.rsslol import (add_rss_feed, get_rss_feeds, is_rss_active, remove_rss_feed, update_rss_feed)

#utils feed
class Feed:
    def __init__(self, feed):
        if not feed.get("entries"):
            return
        entry = feed["entries"][0]
        self.title = entry.get("title") or ""

        # We need title to check latest post
        if not self.title:
            return

        self.link = entry.get("link") or ""
        self.published = entry.get("published") or ""
        self.updated = entry.get("updated") or ""
        self.author = entry.get("author")
        self.summary = entry.get("summary") or ""

    def parsed(self):
        text = f"**Title:** [{self.title.strip()}]({self.link or 'https://google.com'})\n"
        if self.author:
            text += f"**Author:** {self.author}\n"
        if self.published:
            text += f"**Published:** `{self.published}`\n"
        if self.updated:
            text += f"**Last Updated:** `{self.updated}`\n"

        if self.summary and "<div" not in self.summary:
            text += f"**Summary:** {self.summary.strip()}\n"

        if text:
            return "\n".join([i.strip() for i in text.splitlines()])
#utils functions
async def get_http_status_code(url: str) -> int:
    async with aiosession.head(url) as resp:
        return resp.status
      
def get_urls_from_text(text: str) -> bool:
    regex = r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]
                [.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(
                \([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\
                ()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""".strip()
    return [x[0] for x in findall(regex, str(text))]
#main

async def rss_worker():
    print("[INFO]: RSS WORKER STARTED")
    while True:
        feeds = await get_rss_feeds()
        if not feeds:
            await sleep(RSS_DELAY)
            continue

        loop = get_event_loop()

        for _feed in feeds:
            try:
                chat = _feed["chat_id"]
                url = _feed["url"]
                last_title = _feed.get("last_title")

                parsed = await loop.run_in_executor(None, parse, url)
                feed = Feed(parsed)

                if feed.title == last_title:
                    continue

                await app.send_message(
                    chat, feed.parsed(), disable_web_page_preview=True
                )
                await update_rss_feed(chat, feed.title)
            except Exception as e:
                print(str(e), f"RSS {chat}")
                pass
        await sleep(RSS_DELAY)


loop = get_event_loop()
loop.create_task(rss_worker())


@app.on_message(filters.command("add_feed"))
@capture_err
async def add_feed_func(_, m: Message):
    if len(m.command) != 2:
        return await m.reply("Read 'RSS' section in help menu.")
    url = m.text.split(None, 1)[1].strip()

    if not url:
        return await m.reply("[ERROR]: Invalid Argument")

    urls = get_urls_from_text(url)
    if not urls:
        return await m.reply("[ERROR]: Invalid URL")

    url = urls[0]
    status = await get_http_status_code(url)
    if status != 200:
        return await m.reply("[ERROR]: Invalid Url")

    ns = "[ERROR]: This feed isn't supported."
    try:
        loop = get_event_loop()
        parsed = await loop.run_in_executor(None, parse, url)
        feed = Feed(parsed)
    except Exception:
        return await m.reply(ns)
    if not feed:
        return await m.reply(ns)

    chat_id = m.chat.id
    if await is_rss_active(chat_id):
        return await m.reply("[ERROR]: You already have an RSS feed enabled.")
    try:
        await m.reply(feed.parsed(), disable_web_page_preview=True)
    except Exception:
        return await m.reply(ns)
    await add_rss_feed(chat_id, feed.url, feed.title)


@app.on_message(filters.command("rm_feed"))
async def rm_feed_func(_, m: Message):
    if await is_rss_active(m.chat.id):
        await remove_rss_feed(m.chat.id)
        await m.reply("Removed RSS Feed")
    else:
        await m.reply("There are no active RSS Feeds in this chat.")
  
  
  
__MODULE__ = "RSS"
__HELP__ = f"""
/add_feed [URL] - Add a feed to chat
/rm_feed - Remove feed from chat

**Note:**
    - You can only add one feed per chat.
    - Currently RSS and ATOM feeds are supported.
"""
