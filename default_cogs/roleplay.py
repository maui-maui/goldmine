"""Definition of the bot's Roleplay module."""
import random
import discord
from discord.ext import commands
from util.const import adjs, fights, death
from .cog import Cog

class Roleplay(Cog):
    """Commands related to roleplay."""

    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(name='rmember', aliases=['rmem', 'draw'])
    @commands.check(commands.guild_only())
    async def rand_member(self, ctx):
        """Choose a random member from the message's guild."""
        satisfied = False
        m_list = list(ctx.guild.members)
        while not satisfied:
            rmem = random.choice(m_list)
            satisfied = str(rmem.status) == 'online'
        await ctx.send(rmem.mention)
        return rmem

    @commands.command(aliases=['boop', 'poke', 'hit'])
    async def slap(self, ctx, *, target: str):
        """Slap someone, for the win.
        Usage: slap [person]"""
        keystr = '* ' + ctx.message.content.split()[0][len(ctx.prefix):] + 's *'
        await ctx.send('*' + ctx.author.display_name + keystr +
                           target + '* **' + random.choice(adjs) + '**.')

    @commands.command(aliases=['stab', 'kill', 'punch', 'shoot', 'hurt', 'fight'])
    async def attack(self, ctx, *, target: str):
        """Hurt someone with determination in the shot.
        Usage: attack [person]"""
        await ctx.send('*' + ctx.author.display_name + '* ' +
                           random.choice(fights).format('*' + target + '*') + '. '
                           + random.choice(death).format('*' + target + '*'))

    @commands.command()
    async def charlie(self, ctx, *, question: str):
        """Ask a question... Charlie Charlie are you there?
        Usage: charlie [question to ask, without punctuation]"""
        aq = '' if question.endswith('?') else '?'
        await ctx.send('*Charlie Charlie* ' + question + aq + "\n**" +
                           random.choice(['Yes', 'No']) + '**')

    @commands.command(aliases=['soontm'])
    async def soon(self, ctx):
        """Feel the loading of 10000 years, aka Soon™.
        Usage: soon"""
        e = discord.Embed(color=random.randint(1, 255**3-1))
        e.set_image(url='https://images.discordapp.net/.eJwFwdENhCAMANBdGIBiK2dxG4KIJGoN7X1dbnff-7nvON3qDrNHV4Cta5GxeTUZuVXfRNpZ89PVF7kgm-VyXPU2BYwYF6Y0cwgTcsAJMOFMxJESBqblQwgqcvvWd_d_AZ09IXY.TT-FWSP4uhuVeunhP1U44KnCPac')
        await ctx.send(embed=e)

def setup(bot):
    c = Roleplay(bot)
    bot.add_cog(c)
