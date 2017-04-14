from urllib.parse import urlencode
import aiohttp

class GoogleClient:
    def __init__(self, api_key, cse_id):
        self.cse_id = cse_id
        self.api_key = api_key
        self.session = aiohttp.ClientSession()
    def __unload(self):
        self.session.close()

    async def search(self, query):
        url = 'https://www.googleapis.com/customsearch/v1?key=' + self.api_key + \
              '&cx=' + self.cse_id + '&' + urlencode({'q': query}) + '&safe=off'
        async with self.session.get(url) as r:
            resp = await r.json()
        return resp
