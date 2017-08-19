"""Nice selfbot goodies."""
import asyncio
import io
import copy
import sys
import re
import textwrap
import random
from datetime import datetime
import aiohttp
import async_timeout
import discord
from discord.ext.commands.bot import Context, StringView
from discord.ext import commands
from util.perms import echeck_perms
import util.dynaimport as di
pyscreenshot = di.load('pyscreenshot')
scr = di.load('util.screen')
have_pil = True
try:
    from PIL import ImageGrab
except ImportError:
    have_pil = False
from .cog import Cog

class SelfbotGoodies(Cog):
    """Some nice things for selfbot goodies."""

    def __init__(self, bot):
        self.start_time = datetime.now()
        self.web_render = None
        self.re_cache = {}
        self.google_re = re.compile(r'\[\[([a-zA-Z0-9\s]+)\]\]')
        super().__init__(bot)
        self.logger = self.logger.getChild('stuff')

    def __unload(self):
        if self.web_render:
            self.web_render.app.quit()

    @commands.command()
    async def screenshot(self, ctx):
        """Take a screenshot.
        Usage: screenshot"""
        echeck_perms(ctx, ('bot_owner',))
        if have_pil and sys.platform not in ['linux', 'linux2']:
            grabber = ImageGrab
        else:
            grabber = pyscreenshot
        image = grabber.grab()
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        await ctx.send('This is *probably* what my screen looks like right now.', file=discord.File(img_bytes, 'screenshot.png'))

    @commands.command()
    async def render(self, ctx, *, webpage: str):
        """Render a webpage to image.
        Usage: render [url]"""
        echeck_perms(ctx, ('bot_owner',))
        await ctx.send(':warning: Not working. '
                           'Type `yes` quickly if you\'re fine with this crashing.')
        if not (await self.bot.wait_for('message', timeout=6.0,
                                        check=lambda m: m.content.lower().startswith('yes') and m.author == ctx.author and m.channel == ctx.channel)):
            return
        self.web_render = scr.Screenshot()
        image = self.web_render.capture(webpage)
        await ctx.send(file=discord.File(io.BytesIO(image), 'webpage.png'))

    async def on_not_command(self, msg):
        if msg.author.id != self.bot.user.id: return
        if msg.content.startswith('Here are your substitutions:\n`#1`'): return
        if msg.content.startswith('`') or msg.content.endswith('`'): return
        if msg.content.endswith('\u200b'): return
        content = copy.copy(msg.content)
        for sub, rep in self.bot.store['subs'].items():
            text_regexp = r'\b[\*_~]*' + sub + r'[\*_~]*\b'
            if text_regexp in self.re_cache:
                regexp = self.re_cache[text_regexp]
            else:
                regexp = re.compile(text_regexp)
                self.re_cache[text_regexp] = regexp
            replacement = rep
            try:
                content = re.sub(regexp, replacement, content)
            except Exception as e:
                self.logger.error('Substititons: Regexp error. ' + sub)
        if content != msg.content:
            await msg.edit(content=content)
        if 'Google' in self.bot.cogs:
            g_matched = re.finditer(self.google_re, content)
            if g_matched:
                for match in g_matched:
                    msg.content = 'Pgoogle ' + match
                    ctx = self.bot.get_context(msg, 'P')
                    await self.bot.invoke(ctx)

    @commands.group(aliases=['subs'])
    async def sub(self, ctx):
        """Message substitution manager.
        Usage: sub {stuff}"""
        echeck_perms(ctx, ('bot_owner',))
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @sub.command(aliases=['new', 'create', 'make'])
    async def add(self, ctx, replace: str, *, sub: str):
        """Add a substitution.
        Usage: sub add [from] [to]"""
        if replace not in self.bot.store['subs']:
            self.bot.store['subs'][replace] = sub
            await ctx.send('Substitution added!')
        else:
            await ctx.send(':warning: `' + replace + '` is already a substitution!')

    @sub.command(aliases=['ls'])
    async def list(self, ctx):
        """List the substitutions.
        Usage: sub list"""
        if len(self.bot.store['subs']) >= 1:
            pager = commands.Paginator(prefix='', suffix='')
            pager.add_line('Here are your substitutions:')
            for idx, (name, replacement) in enumerate(self.bot.store['subs'].items()):
                pager.add_line('`#' + str(idx + 1) + '`: ' + name + ' → ' + replacement)
            for page in pager.pages:
                await ctx.send(page)
        else:
            await ctx.send('You don\'t have any substitutions!')

    @sub.command(aliases=['mod', 'rewrite', 'change'])
    async def edit(self, ctx, name: str, *, content: str):
        """Edit a substitution.
        Usage: sub edit [substitution] [new content]"""
        try:
            self.bot.store['subs'][name] = content
            await ctx.send('Edited substitution `' + name + '`.')
        except KeyError:
            await ctx.send('No such substitution.')

    @sub.command(aliases=['delete', 'del', 'rm'])
    async def remove(self, ctx, *, name: str):
        """Remove a substitution.
        Usage: sub remove [substitution]"""
        try:
            del self.bot.store['subs'][name]
            await ctx.send('Deleted substitution `' + name + '`.')
        except KeyError:
            await ctx.send('No such substitution.')

    def get_nitro_embed(self):
        emb = discord.Embed(color=0x505e80, description='Discord Nitro is **required** to view this message.')
        emb.set_thumbnail(url='https://images-ext-2.discordapp.net/eyJ1cmwiOiJodHRwczovL2Nkbi5kaXNjb3'
                              'JkYXBwLmNvbS9lbW9qaXMvMjY0Mjg3NTY5Njg3MjE2MTI5LnBuZyJ9.2'
                              '6ZJzd3ReEjyptc_N8jX-00oFGs')
        emb.set_author(name='Discord Nitro Message', icon_url='https://images-ext-1.discordapp.net/eyJ1'
                                       'cmwiOiJodHRwczovL2Nkbi5kaXNjb3JkYXBwLmNvbS9lbW9qaXMvMjYz'
                                       'MDQzMDUxMzM5OTA3MDcyLnBuZyJ9.-pis3JTckm9LcASNN16DaKy9qlI')
        return emb

    @commands.command(hidden=True)
    async def nitro_sendto(self, ctx, *, channel: discord.TextChannel):
        """Send a fake Nitro message embed to a channel.
        Usage: nitro_sendto [channel]"""
        emb = self.get_nitro_embed()
        with channel.typing():
            await asyncio.sleep(random.uniform(0.25, 1.2), loop=self.loop)
            await channel.send(embed=emb)

    @commands.command()
    async def add_emote(self, ctx, emote: str):
        """Add a Twitch, FrankerFaceZ, BetterTTV, or Discord emote to the current guild.
        Usage: add_emote [name of emote]"""
        echeck_perms(ctx, ('bot_owner',))
        emote = emote.replace(':', '')
        with async_timeout.timeout(12):
            try:
                async with self.bot.cog_http.get('https://static-cdn.jtvnw.net/emoticons/v1/' + str(self.bot.emotes['twitch'][emote]['image_id']) + '/1.0') as resp:
                    emote_img = await resp.read()
            except KeyError: # let's try frankerfacez
                try:
                    async with self.bot.cog_http.get('https://cdn.frankerfacez.com/emoticon/' + str(self.bot.emotes['ffz'][emote]) + '/1') as resp:
                        emote_img = await resp.read()
                except KeyError: # let's try BetterTTV
                    try:
                        async with self.bot.cog_http.get(self.bot.emotes['bttv'][emote]) as resp:
                            emote_img = await resp.read()
                    except KeyError: # let's try Discord
                        await ctx.send('**No such emote!** I can fetch from Twitch, FrankerFaceZ, BetterTTV, or Discord (soon).')
                        return False
        result = ctx.guild.create_custom_emoji(emote, emote_img)
        await ctx.send('Added. ' + str(result))

    @commands.command()
    async def gemote_msg(self, ctx, *, text: str):
        """Send a message with emotes, bypassing the cross guild emote restriction.
        Usage: gemote_msg [message]"""
        echeck_perms(ctx, ('bot_owner',))
        emb = discord.Embed(color=random.randint(1, 255**3-1))
        final = text[:]
        for emoji in self.bot.emojis:
            final = final.replace(':%s:' % emoji.name, str(emoji).replace(':', ';_!:'))
        final = final.replace(';_!:', ':')
        emb.description = final
        await ctx.send(embed=emb)

def setup(bot):
    if 'subs' not in bot.store:
        bot.store['subs'] = {}
    bot.add_cog(SelfbotGoodies(bot))
