"""Miscellaneous stuff."""
from discord.ext import commands
from .cog import Cog

class Misc(Cog):
    """Random commands that can be useful here and there.
    This can be... truly random. Don't be scared! 😄
    """

    @commands.command()
    async def lmgtfy(self, ctx, *terms: str):
        """Generate a Let Me Google That For You link.
        Usage: lmgtfy [search terms]"""
        await ctx.send('http://lmgtfy.com/?q=' + '+'.join(terms.replace('+', '%2B')))

    @commands.command()
    async def buzz(self, ctx, *count: int):
        """Barry Bee Benson Buzz :smirk:
        Usage: buzz"""
        fn_i = 8
        if count:
            fn_i = count[0]
        await ctx.send('\n'.join(reversed(['buzz ' * i for i in range(fn_i)])))

    @commands.command()
    async def test(self, ctx):
        """Do a basic test of the bot.
        Usage: test"""
        await ctx.send(ctx.mention + ' Everything is looking good! :smiley:')

def setup(bot):
    c = Misc(bot)
    bot.add_cog(c)
