"""Aiohttp cleverbot.io API library."""
import json
import asyncio
import aiohttp

class CleverBot:
    def __init__(self, user, key, async_init=True, loop=None):
        self.body = {
            'user': user,
            'key': key
        }
        self.conversation = []
        if loop is None:
            loop = asyncio.get_event_loop()
        if async_init:
            loop.create_task(self.async_init(loop))

    async def async_init(self, loop):
        self.session = aiohttp.ClientSession(loop=loop)
        async with self.session.post('https://cleverbot.io/1.0/create', data=self.body) as r:
            j = await r.json()
            self.body['nick'] = j['nick']

    async def ask(self, text):
        self.body['text'] = text
        self.conversation.append(text)

        async with self.session.post('https://cleverbot.io/1.0/ask',
                                     data=self.body) as resp:
            r = await resp.json()

        if r['status'] == 'success':
            self.conversation.append(r['response'])
            return r['response']
        else:
            return 'Hmm, my brain doesn\'t seem to be working right now.'
