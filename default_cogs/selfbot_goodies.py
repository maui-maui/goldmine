"""Nice selfbot goodies."""
import asyncio
import io
import copy
import sys
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
        if msg.content.startswith('Here are your substitutions:\n`#0`'): return
        content = copy.copy(msg.content)
        for sub, replacement in self.dstore['subs'].items():
            if sub in msg.content:
                content = content.replace(sub, replacement)
        if content != msg.content:
            await self.bot.edit_message(msg, content)

    @commands.group(pass_context=True, aliases=['subs'])
    async def sub(self, ctx):
        """Message substitution manager.
        Usage: sub {stuff}"""
        await echeck_perms(ctx, ('bot_owner',))
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @sub.command()
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
            ct = '\n'.join('`#' + str(pair[0]) + '`: ' + pair[1][0] + ' **→** ' + pair[1][1] for pair in enumerate(self.dstore['subs'].items()))
            await self.bot.say('Here are your substitutions:\n' + ct)
        else:
            await self.bot.say('You don\'t have any substitutions!')

    @sub.command()
    async def remove(self, number: int):
        """Remove a substitution."""
        if number <= 0:
            await self.bot.say('We don\'t have zero or negative substitutions here!')
        else:
            try:
                del self.dstore['subs'][number - 1]
                await self.bot.say('Deleted substitution #' + str(number) + '.')
            except (IndexError, ValueError):
                await self.bot.say('No such substitution.')

def setup(bot):
    if 'subs' not in bot.store.store:
        bot.store.store['subs'] = {}
    bot.add_cog(SelfbotGoodies(bot))

