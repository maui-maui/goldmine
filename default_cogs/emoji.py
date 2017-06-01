"""😄 Emoji! 😂"""
import random
import math
from discord.ext import commands
from util.perms import echeck_perms
from util.const import weird_faces
from .cog import Cog

class Emoji(Cog):
    """😄 Emoji! 😂"""

    @commands.command(aliases=['csay', 'esay', 'coolsay', 'emotesay'])
    async def emotisay(self, ctx, *, text: str):
        """Repeat a message, in emoji (block) letters.
        Usage: emotisay [your text here]"""
        chars = list(text.lower())
        cmap = {
            ' ': '    ',
            '#': ':hash:',
            '!': ':exclamation:',
            '?': ':question:',
            '$': ':heavy_dollar_sign:',
            '-': ':heavy_minus_sign:',
            '.': ':small_blue_diamond:',
            '~': ':wavy_dash:',
            '0': ':zero:',
            '1': ':one:',
            '2': ':two:',
            '3': ':three:',
            '4': ':four:',
            '5': ':five:',
            '6': ':six:',
            '7': ':seven:',
            '8': ':eight:',
            '9': ':nine:',
            '^': ':arrow_up:'
        }
        for i, s in enumerate(chars):
            if s in list('abcdefghijklmnopqrstuvwxyz'):
                chars[i] = ':regional_indicator_' + s + ':'
            if s in cmap:
                chars[i] = cmap[s]
        await ctx.send(str(''.join(chars)), filter=False)

    @commands.command(aliases=['wface', 'weirdface', 'weird', 'weird_face', 'mystery', 'neato', 'neat', 'random'])
    async def face(self, ctx, *numbers: int):
        """Give you a random face. Because really, why not?
        Usage: face"""
        fn_face = ''
        if numbers:
            for i in numbers:
                try:
                    fn_face += weird_faces[i - 1] + '\n'
                except IndexError:
                    await ctx.send('**Face #{0} not found!** There are {1} faces total.'.format(str(i), str(len(weird_faces))))
        else:
            fn_face = random.choice(weird_faces)
        if fn_face:
            await ctx.send(fn_face)

    @commands.command(hidden=True)
    async def emotispam(self, ctx):
        """Spam some emotes! CRASH WARNING!
        Warning: Instant crash for desktop users.
        Only fixable on web or mobile apps.
        Usage: emotispam"""
        echeck_perms(ctx, ('bot_owner',))
        _em = emojis
        r = list(range(0, math.ceil(len(emojis) / 2000)))
        for i in r:
            await ctx.send(_em[:2000])
            _em = _em[2000:]

    @commands.command(aliases=['boom', 'bam', 'kaboom', 'explode', 'exploding', 'explosion'])
    async def bang(self, ctx):
        """Boom!
        Usage: boom"""
        await ctx.send('💥')
    @commands.command(aliases=['cookies', 'cookie!'])
    async def cookie(self, ctx):
        """Cookie time!
        Usage: cookie"""
        await ctx.send('🍪')
    @commands.command()
    async def pleb(self, ctx):
        """(╯°□°）╯︵ ┻━┻
        Usage: pleb"""
        await ctx.send('You\'re the pleb here!')
    @commands.command(aliases=['tri'])
    async def triforce(self, ctx):
        """Zelda triforce...
        Usage: triforce"""
        await ctx.send('''**```fix
 ▲
▲ ▲```**''')
    @commands.command(aliases=['triggerd'])
    async def triggered(self, ctx):
        """TRIGGERED!!
        Usage: triggered"""
        await ctx.send('***TRIGGERED***')
    @commands.command()
    async def lenny(self, ctx):
        """Le Lenny Face.
        Usage: lenny"""
        await ctx.send('( ͡° ͜ʖ ͡°)')

def setup(bot):
    """Set up the cog."""
    bot.add_cog(Emoji(bot))
