"""Definition of the bot's Luck module.'"""
import asyncio
import random

from discord.ext import commands
from .cog import Cog

class Luck(Cog):
    """Commands that require some luck to use.
    Lose the coin toss for me, will you?
    """

    @commands.command(aliases=['choice', 'rand'])
    async def choose(self, ctx, *choices: str):
        """Chooses between choices given.
        Usage: choose [choice 1] [choice 2] [choice 3] [etc...]"""
        if len(choices) > 1:
            await ctx.send(random.choice(choices))
        else:
            await ctx.send(':warning: You need at least 2 choices.')

    @commands.command(aliases=['flipcoin', 'coin', 'coinflip', 'cointoss', 'tosscoin'])
    async def flip(self, ctx):
        """Flip a virtual coin.
        Usage: flip"""
        await ctx.send('The coin toss revealed... ' + random.choice(['heads', 'tails']) + '!')

    @commands.command(aliases=['dice', 'rolldice', 'rolld', 'droll', 'diceroll'])
    async def roll(self, ctx, *dice: str):
        """Rolls a virtual dice in [# of rolls]d[Range: 1-N] format.
        Usage: roll [number of rolls]d[max number, normally 6]"""
        if dice:
            try:
                rolls, limit = map(int, dice[0].split('d'))
            except ValueError:
                await ctx.send('Format has to be in NdN!')
                return
        else:
            await ctx.send(random.choice(list('123456')))

        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(result)

    @commands.command(name='8ball', aliases=['8', 'ball', 'eight'])
    async def eight_ball(self, ctx, *, question: str):
        """A magic 8 ball!
        Usage: 8ball [question]"""
        options = [
            'Yes, definitely!',
            'Of course!',
            'Yes!',
            'Probably.',
            "Hmm, I'm not sure...",
            "I'm not sure...",
            "I don't think so.",
            "Hmm, I don't really think so.",
            'Definitely not.',
            'No.',
            'Probably not.',
            'Sure!',
            'Try again later...',
            "I don't know.",
            'Maybe...',
            'Yes, of course!',
            'No, probably not.'
        ]
        await ctx.send(ctx.mention + ' ' + random.choice(options))

def setup(bot):
    c = Luck(bot)
    bot.add_cog(c)
