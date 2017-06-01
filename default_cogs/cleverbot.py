"""Good ol' Cleverbot."""
import asyncio
import random
from util.cleverbot import CleverBot
from discord.ext import commands
from util.perms import or_check_perms
from util.func import bdel
from .cog import Cog

try:
    from d_props import clever_auth
except ImportError:
    clever_auth = ()

class Cleverbot(Cog):
    """Good ol' Cleverbot."""
    def __init__(self, bot):
        super().__init__(bot)
        try:
            self.cb = CleverBot(*clever_auth, loop=self.loop)
        except TypeError:
            class FakeClever:
                @staticmethod
                async def ask():
                    return 'The bot owner hasn\'t set up Cleverbot.'
            self.cb = FakeClever
        self.cleverbutt_timers = set()
        self.cleverbutt_latest = {}
        self.cleverbutt_replied_to = set()
        self.logger = self.logger.getChild('cleverbot')

    def __unload(self):
        try:
            self.cb.session.close()
        except Exception:
            pass

    async def askcb(self, query):
        """Cleverbot query helper."""
        try:
            return await self.cb.ask(query)
        except IndexError:
            return 'Couldn\'t get a response from Cleverbot.'

    async def auto_cb_convo(self, msg, kickstart, replace=False):
        """Cleverbot auto conversation manager."""
        with msg.channel.typing():
            lmsg = msg.content.lower().replace('@everyone', 'everyone').replace('@here', 'here')
            for m in msg.mentions:
                lmsg = lmsg.replace(m.mention, m.display_name)
            if replace:
                cb_string = lmsg.replace(kickstart, '')
            else:
                cb_string = bdel(lmsg, kickstart)
            reply_bot = await self.askcb(cb_string)
            await msg.channel.send(msg.author.mention + ' ' + reply_bot)

    async def clever_reply(self, msg):
        """Cleverbutts handler."""
        self.cleverbutt_timers.add(msg.guild.id)
        with msg.channel.typing():
            await asyncio.sleep(random.random() * 1.8)
            try:
                query = self.cleverbutt_latest[msg.guild.id]
            except KeyError:
                query = msg.content
            reply_bot = await self.askcb(query)
            s_duration = (((len(reply_bot) / 15) * 1.4) + random.random()) - 0.2
            await asyncio.sleep(s_duration / 1.5)
            await msg.channel.send(reply_bot)
        await asyncio.sleep(0.5)
        try:
            del self.cleverbutt_latest[msg.guild.id]
        except Exception:
            pass
        self.cleverbutt_replied_to.add(msg.id)
        self.cleverbutt_timers.remove(msg.guild.id)

    async def on_bot_message(self, msg):
        """Cleverbutt message handling magic."""
        if str(msg.channel) == 'cleverbutts':
            if msg.guild.id in self.cleverbutt_timers: # still on timer for next response
                self.cleverbutt_latest[msg.guild.id] = msg.content
            else:
                await self.clever_reply(msg)

    async def on_mention(self, msg):
        """Cleverbot on-mention logic."""
        if msg.guild.id == 110373943822540800: return
        await self.auto_cb_convo(msg, self.bot.user.mention, replace=True)

    async def on_not_command(self, msg):
        """Cleverbutts kickstarting logic."""
        if msg.channel.name == 'cleverbutts':
            if msg.content.lower() == 'kickstart':
                await msg.channel.send('Hi, how are you doing?')
                return

    async def on_pm(self, msg):
        """PM replying logic."""
        if msg.content.startswith('`'):
            if 'REPL' in self.bot.cogs:
                if msg.channel.id in self.bot.cogs['REPL'].sessions:
                    return
        await msg.channel.trigger_typing()
        c = msg.content
        for m in msg.mentions:
            c = c.replace(m.mention, m.display_name)
        cb_reply = await self.askcb(c)
        return await msg.channel.send(':speech_balloon: ' + cb_reply)

    async def on_prefix_convo(self, msg, lbname):
        """Reply to prefix conversation."""
        return await self.auto_cb_convo(msg, lbname)

    @commands.command(aliases=['cb', 'ask', 'ai', 'bot'])
    async def cleverbot(self, ctx, *, query: str):
        """Queries the Cleverbot service. Because why not.
        Usage: cleverbot [message here]"""
        try:
            reply_bot = await self.askcb(query)
        except IndexError:
            reply_bot = '**Couldn\'t get a response from Cleverbot!**'
        await ctx.send(reply_bot)

    @commands.group(no_pm=True, aliases=['cleverbutts', 'cbs'])
    async def cleverbutt(self, ctx):
        """Manage Cleverbutt stuff.
        Usage: cleverbutt [subcommand] {arguments}"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @cleverbutt.command(no_pm=True, name='start', aliases=['kickstart'])
    async def cleverbutt_kickstart(self, ctx, *msg: str):
        """Kickstart / start cleverbutts conversation
        Usage: cleverbutt start {optional: message}"""
        or_check_perms(ctx, ['manage_guild', 'manage_channels', 'manage_messages'])
        c_map = {c.name: c for c in ctx.guild.channels}
        if 'cleverbutts' in c_map:
            ch = c_map['cleverbutts']
            if msg:
                await ch.send(' '.join(msg))
            else:
                await ch.send('Hello, what\'re you up to?')
            await ctx.send('**Message sent in <#%s>!**' % str(ch.id))
        else:
            await ctx.send('**There\'s no** `#cleverbutts` **channel in this guild!**')

def setup(bot):
    """Set up the cog."""
    bot.add_cog(Cleverbot(bot))
