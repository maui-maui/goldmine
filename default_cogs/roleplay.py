"""Definition of the bot's Roleplay module."""
import random
import discord
import util.commands as commands
from util.const import adjs, fights, death
from .cog import Cog

class Roleplay(Cog):
    """Commands related to roleplay.
    Examples: poking, stabbing, and color roles.
    """

    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(pass_context=True, name='rmember', aliases=['randmember', 'randommember', 'randmem', 'rmem', 'draw'], no_pm=True)
    async def rand_member(self, ctx):
        """Choose a random member from the message's server."""
        satisfied = False
        m_list = list(ctx.message.server.members)
        while not satisfied:
            rmem = random.choice(m_list)
            satisfied = str(rmem.status) == 'online'
        await ctx.bot.say(rmem.mention)
        return rmem

    @commands.command(pass_context=True, aliases=['boop', 'poke', 'hit'])
    async def slap(self, ctx, target: str):
        """Slap someone for the win.
        Usage: slap [person]"""
        keystr = '* ' + ctx.message.content.split()[0][len(ctx.prefix):] + 's *'
        await self.bot.say('*' + ctx.message.author.display_name + keystr +
                           target + '* **' + random.choice(adjs) + '**.')

    @commands.command(pass_context=True, aliases=['stab', 'kill', 'punch', 'shoot', 'hurt', 'fight'])
    async def attack(self, ctx, target: str):
        """Hurt someone with determination in the shot.
        Usage: attack [person]"""
        await self.bot.say('*' + ctx.message.author.display_name + '* ' +
                           random.choice(fights).format('*' + target + '*') + '. '
                           + random.choice(death).format('*' + target + '*'))

    @commands.command()
    async def charlie(self, *, question: str):
        """Ask a question... Charlie Charlie are you there?
        Usage: charlie [question to ask, without punctuation]"""
        aq = '' if question.endswith('?') else '?'
        await self.bot.say('*Charlie Charlie* ' + question + aq + "\n**" +
                           random.choice(['Yes', 'No']) + '**')

    @commands.command(pass_context=True)
    async def mentionme(self, ctx):
        """Have the bot mention yourself. Useful for testing.
        Usage: mentionme"""
        await self.bot.say('Hey there, ' + ctx.message.author.mention + '!')

    @commands.command(pass_context=True, no_pm=True)
    async def mention(self, ctx, *, target: discord.Member):
        """Make the bot mention someone. Useful for testing.
        Usage: mention [mention, nickname, DiscordTag, or username]"""
        await self.bot.say('Hey there, ' + target.mention + '!')

    @commands.command(pass_context=True, aliases=['soontm', 'tm'])
    async def soon(self, ctx):
        """Feel the loading of 10000 years, aka Soon™.
        Usage: soon"""
        e = discord.Embed(color=random.randint(1, 255**3-1))
        e.set_image(url='https://images.discordapp.net/.eJwFwdENhCAMANBdGIBiK2dxG4KIJGoN7X1dbnff-7nvON3qDrNHV4Cta5GxeTUZuVXfRNpZ89PVF7kgm-VyXPU2BYwYF6Y0cwgTcsAJMOFMxJESBqblQwgqcvvWd_d_AZ09IXY.TT-FWSP4uhuVeunhP1U44KnCPac')
        await self.bot.say(embed=e)

def setup(bot):
    c = Roleplay(bot)
    bot.add_cog(c)
