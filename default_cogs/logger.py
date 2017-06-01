"""The bot's chatlogger for AI training."""
import asyncio
import os
from datetime import datetime
import aiohttp
import async_timeout
from discord.ext import commands
from util.perms import echeck_perms
from util.func import async_write
from .cog import Cog

class Logger(Cog):
    """Chat logger for collecting AI training data."""

    def __init__(self, bot):
        super().__init__(bot)
        self.int = 6 * 60
        self.log = {}
        self.w_task = self.loop.create_task(self.writer())
        self.active = True

    def __unload(self):
        self.w_task.cancel()
        self.loop.create_task(self.write(background=False))

    async def on_message(self, msg):
        """Log messages."""
        if not self.active: return
        try:
            self.log[msg.channel.id].append(msg.content)
            if msg.attachments:
                path = os.path.join(self.bot.dir, 'data', 'logger', 'attachments', str(msg.channel.id))
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                file = os.path.join(path, timestamp + '-' + msg.attachments[0].filename[:75])
                if not os.path.exists(path):
                    os.makedirs(path)
                msg.attachments[0].save(os.path.join(path, file))
        except (KeyError, AttributeError):
            self.log[msg.channel.id] = [msg.content]

    async def write(self, background=True):
        """Commit logs to disk."""
        t_len = 0
        for channel in self.log:
            ct = '\n'.join(self.log[channel])
            lct = len(ct)
            t_len += lct
            if lct:
                coro = async_write(os.path.join(self.bot.dir, 'data', 'logger', str(channel) + '.log'),
                                   'ab', b'\n' + ct.encode('utf-8'), self.loop)
                if background:
                    self.loop.create_task(coro)
                else:
                    await coro
        self.log = {}
        if t_len:
            self.bot.logger.info(f'Wrote {t_len} characters of chatlogs!')
        return t_len

    async def writer(self):
        """Writer task"""
        while True:
            await asyncio.sleep(self.int)
            await self.write()

    @commands.group(aliases=['chatlog', 'log'], name='logger')
    async def cmd_logger(self, ctx):
        """Control panel for the logger.
        Usage: logger {stuff}"""
        echeck_perms(ctx, ('bot_owner',))
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @cmd_logger.command(aliases=['commit', 'save'], name='write')
    async def cmd_write(self, ctx):
        """Commit all the logs to disk.
        Usage: logger write"""
        await ctx.send('**Writing...**')
        s = await self.write()
        await ctx.send('**Wrote `%s` characters**' % str(s))

    @cmd_logger.command()
    async def wstart(self, ctx):
        """Start the 6-min writer task.
        Usage: logger wstart"""
        self.w_task = self.loop.create_task(self.writer())
        await ctx.send('**Started 6-min writer task!**')

    @cmd_logger.command()
    async def wstop(self, ctx):
        """Stop the 6-min writer task.
        Usage: logger wstop"""
        self.w_task.cancel()
        await ctx.send('**Stopped 6-min writer task!**')

    @cmd_logger.command()
    async def start(self, ctx):
        """Start logging messages.
        Usage: logger start"""
        self.active = True
        await ctx.send('**Now logging messages!**')

    @cmd_logger.command()
    async def stop(self, ctx):
        """Stop logging messages.
        Usage: logger stop"""
        self.active = False
        await ctx.send('**No longer logging messages!**')

    @cmd_logger.command()
    async def clast(self, ctx, *count: int):
        """Get the last messages from this channel.
        Usage: logger clast {count}"""
        if not count:
            n = 12
        else:
            n = count[0]
        await ctx.send('\n'.join(self.log[ctx.channel.id][-n:]))

def setup(bot):
    log_dir = os.path.join(bot.dir, 'data', 'logger')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    a_dir = os.path.join(log_dir, 'attachments')
    if not os.path.exists(a_dir):
        os.makedirs(a_dir)
    bot.add_cog(Logger(bot))
