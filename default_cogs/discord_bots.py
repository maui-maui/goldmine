"""guild stats reporting."""
import util.json as json
import aiohttp
import asyncio
import async_timeout
from discord.ext import commands
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
    """Reporter of guild stats to services like Discord Bots."""

    def __init__(self, bot):
        super().__init__(bot)
        self.logger = self.logger.getChild('stats')

    def update(self):
        """Report the current guild count to bot lists."""
        return asyncio.gather(self.update_dbots(), self.update_discordlist(), loop=self.loop)

    async def update_dbots(self):
        if not discord_bots_token:
            self.logger.warning('Tried to contact Discord Bots, but no token set!')
            return False
        data = dict(guild_count=len(self.bot.guilds))
        dest = 'https://bots.discord.pw/api/bots/' + str(self.bot.user.id) + '/stats'
        headers = {
            'Authorization': discord_bots_token,
            'Content-Type': 'application/json'
        }
        with async_timeout.timeout(6):
            async with self.bot.cog_http.post(dest, data=json.dumps(data), headers=headers) as r:
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
            'guilds': len(self.bot.guilds)
        }
        dest = 'https://bots.discordlist.net/api'
        headers = {'Content-Type': 'application/json'}
        with async_timeout.timeout(6):
            async with self.bot.cog_http.post(dest, data=json.dumps(data), headers=headers) as r:
                resp_key = f'(got {r.status} {r.reason})'
                if r.status == 200:
                    self.logger.info('Successfully sent DiscordList our guild count! (got 200 OK)')
                else:
                    self.logger.warning('Failed sending our guild count to DiscordList! ' + resp_key)

    async def on_ready(self):
        return await self.update()
    async def on_guild_join(self, guild):
        return await self.update()
    async def on_guild_remove(self, guild):
        return await self.update()

def setup(bot):
    if bot.selfbot:
        bot.logger.warning('Tried to load cog Discord Bots, but we\'re a selfbot. Not loading.')
    else:
        bot.add_cog(DiscordBots(bot))
