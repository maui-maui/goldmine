"""Awesome cog."""
from discord.ext import commands
from .cog import Cog

class MyCog(Cog):
    """My awesome cog."""

def setup(bot):
    bot.add_cog(MyCog(bot))
