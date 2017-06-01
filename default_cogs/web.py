"""Web dashboard."""
import os
import sys
import json
import aiohttp
from discord.ext import commands
import util.dynaimport as di
from .cog import Cog

japronto = di.load('japronto')
sanic = di.load('sanic')
response = di.load('sanic.response')
root_dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].core_file))
web_root = os.path.join(root_dir, 'assets', 'web')
def webroot(f):
    return os.path.join(web_root, *f.split('/'))

class Web(Cog):
    """The awesome web dashboard."""
    def __init__(self, bot):
        super().__init__(bot)
        self.logger = self.logger.getChild('web')
        self.port = 8085
        self.host = '127.0.0.1'
        self.app = None
        self.server = None
        self.server_task = None
        if bot.user:
            self.loop.create_task(self.start())

    def __unload(self):
        self.guild_task.cancel()

    async def on_ready(self):
        await self.start()

    async def start(self):
        self.logger.info('Starting web server on %s:%s!', self.host, str(self.port))
        app = sanic.Sanic()
        await self.init_app(app)
        self.app = app
        self.server = app.create_server(host=self.host, port=self.port)
        self.server_task = self.loop.create_task(self.server)

    async def init_app(self, app):
        self.logger.info('Initializing app...')
        @app.route('/')
        async def test(req):
            self.logger.info('Got request at /')
            return response.text('hello')
            return response.file(webroot('index.html'))

def setup(bot):
    bot.add_cog(Web(bot))
'''
async def hello(request):
    return request.Response(text='Hello world!')

app = japronto.Application()
app.router.add_route('/', hello)
app.run()'''
