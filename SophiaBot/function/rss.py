import codecs
import pickle
from typing import Dict, List, Union

from SophiaBot import db

rssdb = db.rss

async def add_rss_feed(chat_id: int, url: str, last_title: str):
    return await rsslol.update_one(
        {"chat_id": chat_id},
        {"$set": {"url": url, "last_title": last_title}},
        upsert=True,
    )


async def remove_rss_feed(chat_id: int):
    return await rsslol.delete_one({"chat_id": chat_id})


async def update_rss_feed(chat_id: int, last_title: str):
    return await rsslol.update_one(
        {"chat_id": chat_id},
        {"$set": {"last_title": last_title}},
        upsert=True,
    )


async def is_rss_active(chat_id: int) -> bool:
    return await rsslol.find_one({"chat_id": chat_id})


async def get_rss_feeds() -> list:
    feeds = rsslol.find({"chat_id": {"$exists": 1}})
    feeds = await feeds.to_list(length=10000000)
    if not feeds:
        return
    data = []
    for feed in feeds:
        data.append(
            dict(
                chat_id=feed["chat_id"],
                url=feed["url"],
                last_title=feed["last_title"],
            )
        )
    return data


async def get_rss_feeds_count() -> int:
    feeds = rsslol.find({"chat_id": {"$exists": 1}})
    feeds = await feeds.to_list(length=10000000)
    return len(feeds)
