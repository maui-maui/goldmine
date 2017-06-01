"""Google!"""
import random
import discord
from discord.ext import commands
from util.google_old import search
from util.google import GoogleClient
from .cog import Cog

try:
    from d_props import google_api_key as GOOGLE_API_KEY
except ImportError:
    GOOGLE_API_KEY = None

class Google(Cog):
    """Google. We all need it at some point."""
    CSE_ID = '011887893391472424519:xf_tuvgfrgk'

    def __init__(self, bot):
        super().__init__(bot)
        if GOOGLE_API_KEY:
            self.gclient = GoogleClient(GOOGLE_API_KEY, self.CSE_ID)
        else:
            self.gclient = None
        self.logger = self.logger.getChild('google')

    def s_google(self, query, num=3):
        """A method of querying Google safe for async."""
        return search(query, num=num)

    @commands.command(aliases=['g', 'search', 'query', 'q'])
    async def google(self, ctx, *text: str):
        """Search something on Google.
        Usage: google [search terms]"""
        if text:
            query = ' '.join(text)
        else:
            await ctx.send(ctx.mention + ' You need to specify some search terms!')
            return
        m = ''
        emb = discord.Embed(color=random.randint(1, 255**3-1))
        emb.set_author(icon_url='https://raw.githubusercontent.com/Armored-Dragon/goldmine/master/assets/icon-google.png', name='Google', url='https://google.com/')
        if query in self.bot.store['google_cache']:
            fql = self.bot.store['google_cache'][query]
            r = fql[0]
            emb.title = r['title']
            emb.description = r['snippet']
            emb.add_field(name='Link', value=r['link'])
            try:
                emb.set_image(url=r['pagemap']['metatags'][0]['og:image'])
            except KeyError:
                try:
                    emb.set_image(url=r['pagemap']['metatags'][0]['twitter:image'])
                except KeyError:
                    pass
        elif self.gclient:
            resp = await self.gclient.search(query)

            if 'items' in resp:
                fql = resp['items']
                if fql:
                    self.bot.store['google_cache'][query] = fql
                    r = fql[0]
                    emb.title = r['title']
                    emb.description = r['snippet']
                    emb.add_field(name='Link', value=r['link'])
                    try:
                        emb.set_image(url=r['pagemap']['metatags'][0]['og:image'])
                    except KeyError:
                        try:
                            emb.set_image(url=r['pagemap']['metatags'][0]['twitter:image'])
                        except KeyError:
                            pass
                else:
                    emb.title = 'Google Search'
                    emb.description = 'Nothing was found.'
            elif 'error' in resp:
                emb.title = 'Google Search'
                emb.description = "I've reached the max number of searches for the day. Try again tomorrow."
                self.logger.info(resp)
                return
            elif 'searchInformation' in resp and int(resp['searchInformation']['totalResults']) < 1:
                emb.title = 'Google Search'
                emb.description = 'Nothing was found.'
            else:
                emb.title = 'Google Search'
                emb.description = 'The response seems to have been invalid. Try again later?'
                self.logger.info(resp)
        else:
            fql = await self.s_google(query, num=1)
            emb.title = 'Google Search'
            if fql:
                emb.description = '\u200b'
                emb.add_field(name='Link', value=fql[0])
                self.bot.store['google_cache'][query] = fql
            else:
                emb.description = 'Nothing was found.'
        await ctx.send(embed=emb)

def setup(bot):
    if 'google_cache' not in bot.store:
        bot.store['google_cache'] = {}
    bot.add_cog(Google(bot))
