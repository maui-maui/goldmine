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
import util.commands as commands
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
        super().__init__(bot)
        self.logger = self.logger.getChild('stuff')

    def __unload(self):
        if self.web_render:
            self.web_render.app.quit()

    @commands.command(pass_context=True)
    async def screenshot(self, ctx):
        """Take a screenshot.
        Usage: screenshot"""
        echeck_perms(ctx, ('bot_owner',))
        if have_pil and (sys.platform not in ['linux', 'linux2']):
            grabber = ImageGrab
        else:
            grabber = pyscreenshot
        image = grabber.grab()
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        await self.bot.upload(img_bytes, filename='screenshot.png', content='This is *probably* what my screen looks like right now.')

    @commands.command(pass_context=True)
    async def render(self, ctx, *, webpage: str):
        """Render a webpage to image.
        Usage: render [url]"""
        echeck_perms(ctx, ('bot_owner',))
        await self.bot.say(':warning: Not yet working.'
                           'Type `yes` within 6 seconds to proceed and maybe crash your bot.')
        if not (await self.bot.wait_for_message(timeout=6.0, author=ctx.message.author,
                                                channel=ctx.message.channel,
                                                check=lambda m: m.content.lower().startswith('yes'))):
            return
        try:
            self.web_render = scr.Screenshot()
        except ImportError:
            await self.bot.say('The bot owner hasn\'t enabled this feature!')
            return
        image = self.web_render.capture(webpage)
        await self.bot.upload(io.BytesIO(image), filename='webpage.png')

    async def on_not_command(self, msg):
        if msg.author.id != self.bot.user.id: return
        if msg.content.startswith('Here are your substitutions:\n`#1`'): return
        if msg.content.startswith('`') or msg.content.endswith('`'): return
        if msg.content.endswith('\u200b'): return
        content = copy.copy(msg.content)
        for sub, rep in self.bot.store['subs'].items():
            regexp = r'\b[\*_~]*' + sub + r'[\*_~]*\b'
            replacement = rep
            try:
                content = re.sub(regexp, replacement, content)
            except Exception as e:
                self.logger.error('Substititons: Regexp error. ' + sub)
        if content != msg.content:
            await self.bot.edit_message(msg, content)

    @commands.group(pass_context=True, aliases=['subs'])
    async def sub(self, ctx):
        """Message substitution manager.
        Usage: sub {stuff}"""
        echeck_perms(ctx, ('bot_owner',))
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @sub.command(aliases=['new', 'create', 'make'])
    async def add(self, replace: str, *, sub: str):
        """Add a substitution.
        Usage: sub add [from] [to]"""
        if replace not in self.bot.store['subs']:
            self.bot.store['subs'][replace] = sub
            await self.bot.say('Substitution added!')
        else:
            await self.bot.say(':warning: `' + replace + '` is already a substitution!')

    @sub.command(aliases=['ls'])
    async def list(self):
        """List the substitutions.
        Usage: sub list"""
        if len(self.bot.store['subs']) >= 1:
            pager = commands.Paginator(prefix='', suffix='')
            pager.add_line('Here are your substitutions:')
            for idx, (name, replacement) in enumerate(self.bot.store['subs'].items()):
                pager.add_line('`#' + str(idx + 1) + '`: ' + name + ' **→** ' + replacement)
            for page in pager.pages:
                await self.bot.say(page)
        else:
            await self.bot.say('You don\'t have any substitutions!')

    @sub.command(aliases=['mod', 'rewrite', 'change'])
    async def edit(self, name: str, *, content: str):
        """Edit a substitution.
        Usage: sub edit [substitution] [new content]"""
        try:
            self.bot.store['subs'][name] = content
            await self.bot.say('Edited substitution `' + name + '`.')
        except KeyError:
            await self.bot.say('No such substitution.')

    @sub.command(aliases=['delete', 'del', 'rm'])
    async def remove(self, *, name: str):
        """Remove a substitution.
        Usage: sub remove [substitution]"""
        try:
            del self.bot.store['subs'][name]
            await self.bot.say('Deleted substitution `' + name + '`.')
        except KeyError:
            await self.bot.say('No such substitution.')

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
    async def nitro_sendto(self, *, channel: discord.Channel):
        """Send a fake Nitro message embed to a channel.
        Usage: nitro_sendto [channel]"""
        emb = self.get_nitro_embed()
        await self.bot.send_typing(channel)
        await asyncio.sleep(random.uniform(0.1, 1.2))
        await self.bot.send_message(channel, embed=emb)

    @commands.command(pass_context=True)
    async def add_emote(self, ctx, _emote: str):
        """Add a Twitch, FrankerFaceZ, BetterTTV, or Discord emote to the current server.
        Usage: add_emote [name of emote]"""
        echeck_perms(ctx, ('bot_owner',))
        emote = _emote.replace(':', '')
        ext = 'png'
        async with aiohttp.ClientSession(loop=self.loop) as session:
            with async_timeout.timeout(13):
                try:
                    async with session.get('https://static-cdn.jtvnw.net/emoticons/v1/' + str(self.bot.emotes['twitch'][emote]['image_id']) + '/1.0') as resp:
                        emote_img = await resp.read()
                except KeyError: # let's try frankerfacez
                    try:
                        async with session.get('https://cdn.frankerfacez.com/emoticon/' + str(self.bot.emotes['ffz'][emote]) + '/1') as resp:
                            emote_img = await resp.read()
                    except KeyError: # let's try BetterTTV
                        try:
                            async with session.get(self.bot.emotes['bttv'][emote]) as resp:
                                emote_img = await resp.read()
                        except KeyError: # let's try Discord
                            await self.bot.say('**No such emote!** I can fetch from Twitch, FrankerFaceZ, BetterTTV, or Discord (soon).')
                            return False
        result = await self.bot.create_custom_emoji(ctx.message.server, name=emote, image=emote_img)
        await self.bot.say('Added. ' + str(result))

    @commands.command(pass_context=True)
    async def gemote_msg(self, ctx, *, text: str):
        """Send a message with emotes, bypassing the cross server emote restriction.
        Usage: gemote_msg [message]"""
        echeck_perms(ctx, ('bot_owner',))
        emb = discord.Embed(color=random.randint(1, 255**3-1))
        final = text[:]
        for emoji in self.bot.get_all_emojis():
            final = final.replace(':%s:' % emoji.name, str(emoji).replace(':', ';_!:'))
        final = final.replace(';_!:', ':')
        emb.description = final
        await self.bot.say(embed=emb)

def setup(bot):
    if 'subs' not in bot.store.store:
        bot.store.store['subs'] = {}
    bot.add_cog(SelfbotGoodies(bot))
