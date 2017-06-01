"""Mod log cog."""
import random
import functools
from datetime import datetime
import discord
from discord.ext import commands
from util.perms import or_check_perms
from util.func import date_suffix
from .cog import Cog

def modevent(orig):
    @functools.wraps(orig)
    async def event_wrap(self, *args, **kwargs):
        if self.bot.selfbot: return
        scope = self
        if args[0].guild.id in scope.bot.store['mod_map']:
            target = args[0].guild.get_channel(scope.bot.store['mod_map'][args[0].guild.id])
            await orig(self, target, *args, **kwargs)
    event_wrap.__name__ = orig.__name__
    event_wrap.__qualname__ = orig.__qualname__
    event_wrap.__doc__ = orig.__doc__
    return event_wrap

class ModLog(Cog):
    """Action logging cog for moderation and such."""

    @commands.group(aliases=['guildlog', 'mod_log', 'guild_log'])
    async def modlog(self, ctx):
        """Moderation log!"""
        if not ctx.invoked_subcommand:
            await self.bot.send_cmd_help(ctx)

    @modlog.command()
    async def test(self, ctx):
        """Make sure the mod log system is up.
        Usage: modlog test"""
        await ctx.send('The mod log system is up and running!')

    @modlog.command()
    async def channel(self, ctx, *, channel: discord.Channel):
        """Set the mod log channel for this guild.
        Usage: modlog channel [channel]"""
        self.bot.store['mod_map'][channel.guild.id] = channel.id
        await ctx.send('Mod log channel set! Now sending a test message to ' + channel.mention + '.')
        await channel.send(embed=discord.Embed(title='Testing'))

    @modevent
    async def on_message_delete(self, target, msg):
        emb = discord.Embed(color=random.randint(0, 255**3-1))
        emb.title = 'Message by **' + str(msg.author) + '** deleted'
        emb.set_author(name=str(msg.author), icon_url=msg.author.avatar_url)
        content = '`' + msg.content + '`'
        truncate = '...'
        if len(content) > 1024:
            content = content[:1024 - len(truncate)] + truncate
        emb.add_field(name='Channel', value=msg.channel.mention)
        emb.add_field(name='Content', value=content)
        now = datetime.now()
        key = date_suffix(now.strftime('%-d'))
        emb.set_footer(text=now.strftime('%A %B %-d{key}, %Y at %-I:%M %p'.format(key=key)), icon_url=self.bot.avatar_link)
        await target.send(embed=emb)

def setup(bot):
    try:
        bot.store['mod_map']
    except KeyError:
        bot.store['mod_map'] = {}
#    if 'mod_map' not in bot.store.store:
#        bot.store['mod_map'] = {}
    bot.add_cog(ModLog(bot))
