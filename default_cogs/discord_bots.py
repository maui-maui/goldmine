"""Server stats reporting."""
import util.json as json
import aiohttp
import async_timeout
import util.commands as commands
from .cog import Cog

try:
    from ex_props import discord_bots_token
except ImportError:
    discord_bots_token = None
try:
    from ex_props import discordlist_token
except ImportError:
    discordlist_token = None

class DiscordBots(Cog):
    """Reporter of server stats to services like Discord Bots."""

    def __init__(self, bot):
        self.http = None
        super().__init__(bot)
        self.logger = self.logger.getChild('stats')
        self.loop.create_task(self.init_http())

    def __unload(self):
        self.http.close()

    async def init_http(self):
        self.http = aiohttp.ClientSession()

    def update(self):
        """Report the current server count to bot lists."""
        return asyncio.gather(self.update_dbots(), self.update_discordlist(), loop=self.loop)

    async def update_dbots(self):
        if not discord_bots_token:
            self.logger.warning('Tried to contact Discord Bots, but no token set!')
            return False
        data = dict(server_count=len(self.bot.servers))
        dest = 'https://bots.discord.pw/api/bots/' + self.bot.user.id + '/stats'
        headers = {
            'Authorization': discord_bots_token,
            'Content-Type': 'application/json'
        }
        with async_timeout.timeout(6):
            async with self.http.post(dest, data=json.dumps(data), headers=headers) as r:
                resp_key = f'(got {r.status} {r.reason})'
                if r.status == 200:
                    self.logger.info('Successfully sent Discord Bots our guild count (got 200 OK)')
                else:
                    self.logger.warning('Failed sending our guild count to Discord Bots! ' + resp_key)

    async def update_discordlist(self):
        if not discordlist_token:
            self.logger.warning('Tried to contact DiscordList, but no token set!')
            return False
        data = {
            'token': discordlist_token,
            'servers': len(self.bot.servers)
        }
        dest = 'https://bots.discordlist.net/api'
        headers = {'Content-Type': 'application/json'}
        with async_timeout.timeout(6):
            async with self.http.post(dest, data=json.dumps(data), headers=headers) as r:
                resp_key = f'(got {r.status} {r.reason})'
                if r.status == 200:
                    self.logger.info('Successfully sent DiscordList our guild count! (got 200 OK)')
                else:
                    self.logger.warning('Failed sending our guild count to DiscordList! ' + resp_key)

    async def on_ready(self):
        return await self.update()
    async def on_server_join(self, server):
        return await self.update()
    async def on_server_remove(self, server):
        return await self.update()

def setup(bot):
    if bot.selfbot:
        bot.logger.warning('Tried to load cog Discord Bots, but we\'re a selfbot. Not loading.')
    else:
        bot.add_cog(DiscordBots(bot))
