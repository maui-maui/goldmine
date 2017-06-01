"""Async xkcd library."""
from .json import loads as jloads
import random
import async_timeout
import aiohttp

XKCD_URL = 'http://www.xkcd.com/'
IMAGE_URL = 'http://imgs.xkcd.com/comics/'
EXPLAIN_URL = 'http://explainxkcd.com/'
LINK_OFFSET = len(IMAGE_URL)

class Comic(object):
    """xkcd comic."""
    def __init__(self, number):
        self.number = number
        if number <= 0:
            raise InvalidComic('%s is not a valid comic' % str(number))

        self.link = XKCD_URL + str(number)
        self.jlink = self.link + '/info.0.json'
        self.explain_url = EXPLAIN_URL + str(number)

    async def async_init(self):
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(6.5):
                async with session.get(self.jlink) as r:
                    xkcd = await r.text()
        data = jloads(xkcd)
        self.title = data['safe_title']
        self.alt_text = data['alt']
        self.image_link = data['img']
        index = self.image_link.find(IMAGE_URL)
        self.image_name = self.image_link[index + LINK_OFFSET:]

    async def fetch(self):
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(6.5):
                async with session.get(self.image_link) as r:
                    return await r.read()

class InvalidComic(Exception):
    pass

async def latest_comic_num():
    async with aiohttp.ClientSession() as session:
        with async_timeout.timeout(6.5):
            async with session.get('http://xkcd.com/info.0.json') as r:
                xkcd = await r.text()
    return jloads(xkcd)['num']

async def random_comic():
    random.seed()
    num_comics = await latest_comic_num()
    comic = Comic(random.randint(1, num_comics))
    await comic.async_init()
    return comic

async def get_comic(number):
    num_comics = await latest_comic_num()
    if number > num_comics or number <= 0:
        raise InvalidComic('%s is not a valid comic' % str(number))
    comic = Comic(number)
    await comic.async_init()
    return comic

async def latest_comic():
    number = await latest_comic_num()
    comic = Comic(number)
    await comic.async_init()
    return comic
