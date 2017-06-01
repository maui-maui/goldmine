"""Nice and easy... custom commands!"""
from discord.ext import commands
from .cog import Cog

class CustomCommands(Cog):
    """Nice and easy... custom commands!"""

    @commands.command(aliases=['ny', 'nyet', 'noty'])
    async def notyet(self, ctx):
        """Not yet, coming Soon™!"""
        await ctx.send('⚠ Not finished yet!')

def setup(bot):
    bot.add_cog(CustomCommands(bot))
