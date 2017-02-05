"""Nice selfbot goodies."""
import asyncio
import io
import copy
import sys
import re
import textwrap
from datetime import datetime
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

    def __unload(self):
        if self.web_render:
            self.web_render.app.quit()

    @commands.command(pass_context=True)
    async def screenshot(self, ctx):
        """Take a screenshot.
        Usage: screenshot"""
        await echeck_perms(ctx, ('bot_owner',))
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
    async def msg_rate(self, ctx):
        """Get the message rate.
        Usage: msg_rate"""
        await echeck_perms(ctx, ('bot_owner',))
        msg = await self.bot.say('Please wait...')
        start_time = datetime.now()
        m = {'messages': 0}
        async def msg_task(m):
            while True:
                await self.bot.wait_for_message()
                m['messages'] += 1
        task = self.loop.create_task(msg_task(m))
        await asyncio.sleep(8)
        task.cancel()
        time_elapsed = datetime.now() - start_time
        time_elapsed = time_elapsed.total_seconds()
        await self.bot.edit_message(msg, 'I seem to be getting ' + str(round(m['messages'] / time_elapsed, 2)) + ' messages per second.')

    @commands.command(pass_context=True)
    async def render(self, ctx, *, webpage: str):
        """Render a webpage to image.
        Usage: render [url]"""
        await echeck_perms(ctx, ('bot_owner',))
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
        if msg.content.startswith('```') or msg.content.endswith('```'): return
        if msg.content.endswith('\u200b'): return
        content = copy.copy(msg.content)
        for sub, replacement in self.dstore['subs'].items():
            content = re.sub(r'\b[\*_~]*' + sub + r'[\*_~]*\b', replacement, content)
        if content != msg.content:
            await self.bot.edit_message(msg, content)

    @commands.group(pass_context=True, aliases=['subs'])
    async def sub(self, ctx):
        """Message substitution manager.
        Usage: sub {stuff}"""
        await echeck_perms(ctx, ('bot_owner',))
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @sub.command(aliases=['new', 'create', 'make'])
    async def add(self, replace: str, *, sub: str):
        """Add a substitution.
        Usage: sub add [from] [to]"""
        if replace not in self.dstore['subs']:
            self.dstore['subs'][replace] = sub
            await self.bot.say('Substitution added!')
        else:
            await self.bot.say(':warning: `' + replace + '` is already a substitution!')

    @sub.command(aliases=['ls'])
    async def list(self):
        """List the substitutions.
        Usage: sub list"""
        if len(self.dstore['subs']) >= 1:
            pager = commands.Paginator(prefix='', suffix='')
            pager.add_line('Here are your substitutions:')
            for idx, (name, replacement) in enumerate(self.dstore['subs'].items()):
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
            self.dstore['subs'][name] = content
            await self.bot.say('Edited substitution `' + name + '`.')
        except KeyError:
            await self.bot.say('No such substitution.')

    @sub.command(aliases=['delete', 'del', 'rm'])
    async def remove(self, *, name: str):
        """Remove a substitution.
        Usage: sub remove [substitution]"""
        try:
            del self.dstore['subs'][name]
            await self.bot.say('Deleted substitution `' + name + '`.')
        except KeyError:
            await self.bot.say('No such substitution.')

    @commands.command(pass_context=True, aliases=['ttsspam', 'tts_spam'])
    async def ttspam(self, ctx, *, text: str):
        """Spam a message with TTS. **This may get you banned from some servers.**
        Usage: ttspam [message]"""
        await echeck_perms(ctx, ('bot_owner',))
        m = await self.bot.say(textwrap.wrap((text + ' ') * 2000, width=2000)[0], tts=True)
        await asyncio.sleep(0.1)
        await self.bot.delete_message(m)

def setup(bot):
    if 'subs' not in bot.store.store:
        bot.store.store['subs'] = {}
    bot.add_cog(SelfbotGoodies(bot))

