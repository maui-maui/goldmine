"""Google!"""
import random
import discord
import util.commands as commands
from util.google import search
from .cog import Cog

class Google(Cog):
    """Google. We all need it at some point."""

    async def s_google(self, query, num=3):
        """A method of querying Google safe for async."""
        return await search(query, num=num)

    @commands.command(aliases=['g', 'search', 'query', 'q'])
    async def google(self, *text: str):
        """Search something on Google.
        Usage: google [search terms]"""
        if text:
            query = ' '.join(text)
        else:
            await self.bot.reply('you need to specify some search terms!')
            return
        m = ''
        fql = await self.s_google(query, num=2)
        emb = discord.Embed(color=int('0x%06X' % random.randint(1, 255**3-1), 16), title='Search Results')
        emb.description = '\u200b'
        emb.set_author(icon_url='https://raw.githubusercontent.com/Armored-Dragon/goldmine/master/assets/google.png', name='Google')
        if fql:
            emb.add_field(name='Link', value=fql[0], inline=False)
            if len(fql) > 1:
                emb.add_field(name='Another Link', value=fql[1], inline=False)
        else:
            emb.description += 'Nothing was found.'
        await self.bot.say(embed=emb)

def setup(bot):
    bot.add_cog(Google(bot))
