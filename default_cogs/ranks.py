"""Ranks and levels."""
import math
import random
from contextlib import suppress
import discord
from discord.ext import commands
import util.ranks as rank
from util.const import lvl_base, bool_true
from util.fake import FakeMessageMember
from .cog import Cog

class Ranks(Cog):
    """Ranks and levels."""

    async def on_not_command(self, msg):
        """Do level-up logic."""
        if self.bot.selfbot: return
        if isinstance(msg.channel, discord.abc.PrivateChannel): return
        if msg.author.bot: return
        prof_name = 'profile_' + str(msg.guild.id)
        prof = self.bot.store.get_prop(msg, prof_name)
        prof['exp'] += math.ceil(((len(msg.content) / 6) * 1.5) + random.randint(0, 14))
        new_level = rank.xp_level(prof['exp'])[0]
        if new_level > prof['level']:
            bclu = self.bot.store.get_prop(msg, 'broadcast_level_up')
            if isinstance(bclu, str):
                bclu = bclu.lower()
            if bclu in bool_true:
                await msg.channel.send('**Hooray!** {0.mention} has just *advanced* to **level {1}**.'.format(msg.author, str(new_level)))
        prof['level'] = new_level
        self.bot.store.set_prop(msg, 'by_user', prof_name, prof)

    @commands.command(aliases=['xp', 'level', 'lvl', 'exp', 'levels'])
    @commands.check(commands.guild_only())
    async def rank(self, ctx, *, user: discord.Member):
        """Check experience, level, and rank!
        Usage: xp {user}"""
        stat_fmt = '''{0.author.mention} Here are {5} **stats**:
**LEVEL: {1}
EXPERIENCE: __{2}/{3}__ for next level
TOTAL EXPERIENCE: {4}**
*Try getting some more! :smiley:*
'''
        target = FakeMessageMember(user)
        prof = self.bot.store.get_prop(target, 'profile_' + str(target.guild.id))
        rlevel = rank.xp_level(prof['exp'])
        await ctx.send(stat_fmt.format(target, str(rlevel[0]), str(int(rlevel[1])),
                                           str(int((rlevel[0] + 1) * lvl_base)), str(prof['exp']),
                                           ('your' if target.author.id == ctx.author.id else str(target.author) + "'s")))

def setup(bot):
    bot.add_cog(Ranks(bot))
