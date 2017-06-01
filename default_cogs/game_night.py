"""Game night!"""
import asyncio
import discord
from discord.ext import commands
from util.perms import or_check_perms
from .cog import Cog

class GameNight(Cog):
    """Now's your chance to have a quick and easy game night!"""
    def __init__(self, bot):
        self.games = {}
        super().__init__(bot)

    @commands.group(aliases=['game_night'], no_pm=True)
    async def gamenight(self, ctx):
        """Game night!
        Usage: gamenight {stuff}"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @gamenight.command(aliases=['end', 'finish'])
    async def stop(self, ctx):
        """Stop the current game night session.
        Usage: gamenight stop"""
        or_check_perms(ctx, ['manage_guild', 'manage_channels', 'manage_messages', 'manage_roles'])
        if ctx.channel.id in self.games:
            game = self.games[ctx.channel.id]
            if game['role']:
                try:
                    await game['role'].delete(reason='Deleting game night session-specific role')
                except discord.Forbidden:
                    pass
            del self.games[ctx.channel.id]
            await ctx.send('**Ended the current game night session at round ' + str(game['round']) + '.**')
            del game
        else:
            await ctx.send(ctx.mention + ' There\'s no game night session active here!')

    @gamenight.command(aliases=['meme_war', 'meme-war', 'memes', 'meme', 'mwar', 'memwar'])
    async def memewar(self, ctx, *, topic: str):
        """Start a meme war on a topic.
        Usage: gamenight memewar [topic]"""
        or_check_perms(ctx, ['manage_guild', 'manage_channels', 'manage_messages', 'manage_roles'])
        game = {
            'active': False,
            'topic': topic,
            'duration': 1.5 * 60,
            'players': {
                ctx.author: 0
            },
            'recruiting': True,
            'role': None,
            'round': 1,
            'round_active': False,
            'r_mention': ''
        }
        if ctx.channel.id in self.games:
            await ctx.send(ctx.mention + ' There\'s already a game night session here!')
            return
        self.games[ctx.channel.id] = game
        await ctx.send(f''':clap: Now hosting a **meme war** for `{topic}`! :clap:
We need at least 3 participants. ({ctx.mention} is already in.)
Everyone, you have 1 minute to join! Just use `{ctx.prefix}gamenight join`.''')
        await asyncio.sleep(60, loop=self.loop)
        game['recruiting'] = False
        r_mention = ''
        if len(game['players']) < 3:
            await ctx.send('⚠ **Stopped due to insufficent number of participants.**')
            del self.games[ctx.channel.id]
            return
        try:
            role = await ctx.guild.create_role(name='Game Night Player', color=discord.Color.dark_teal(), mentionable=True,
                                               reason='Creating game night session-specific role')
            for player in game['players']:
                await player.add_roles(role, reason='Adding game night session-specific role for mentioning')
            r_mention = '<@&' + str(role.id) + '> '
            game['role'] = role
        except discord.Forbidden:
            await ctx.send('⚠ **I work best with the Manage Roles permission.**')
        game['r_mention'] = r_mention
        await ctx.send('''Starting the **meme war** in 30 seconds!
{}Get your butts in here, and grab your dankest memes!'''.format(r_mention))
        await asyncio.sleep(28.6, loop=self.loop)
        game['active'] = True
        game['round_active'] = True
        await ctx.send(f'''{r_mention}The **meme war** is now starting for the topic `{topic}`!
Get your memes in already! :clap::clap:
Leaders: when you're ready, select a winner (and end the round) with `{ctx.prefix}gamenight winner`!''')

    @gamenight.command()
    async def topic(self, ctx, *, topic: str):
        """Start the current round with a topic."""
        or_check_perms(ctx, ['manage_guild', 'manage_channels', 'manage_messages', 'manage_roles'])
        if ctx.channel.id in self.games:
            try:
                await ctx.message.delete(reason='Deleting message sent to change the topic, so players don\'t see and prepare before the round')
            except discord.Forbidden:
                await ctx.send('⚠ **I work best with the Manage Messages permission.**')
            game = self.games[ctx.channel.id]
            r_mention = game['r_mention']
            game['topic'] = topic
            await ctx.send('''Starting **round {}** in 30 seconds!
{}Get your butts in here, and grab your dankest memes!'''.format(str(game['round']), r_mention))
            await asyncio.sleep(28.6, loop=self.loop)
            game['active'] = True
            game['round_active'] = True
            await ctx.send(f'''{r_mention}The **meme war** is now starting for the topic `{topic}`!
Get your memes in already! :clap::clap:
Leaders: when you're ready, select a winner (and end the round) with `{ctx.prefix}gamenight winner`!''')
        else:
            await ctx.send(ctx.mention + ' There isn\'t a game night session in this channel!')

    @gamenight.command()
    async def winner(self, ctx, *, winner: discord.Member):
        """Select a winner for a game night session.
        Usage: gamenight winner [winner]"""
        or_check_perms(ctx, ['manage_guild', 'manage_channels', 'manage_messages', 'manage_roles'])
        if ctx.channel.id in self.games:
            try:
                await ctx.message.delete(reason='Deleting message sent to select winner, so players don\'t see the winner until after the drum roll')
            except discord.Forbidden:
                await ctx.send('⚠ **I work best with the Manage Messages permission.**')
            game = self.games[ctx.channel.id]
            if winner in game['players']:
                k = '.'
                key = '**...and the winner is'
                msg = await ctx.send(key + '**')
                for i in range(1, 4):
                    await asyncio.sleep(0.96, loop=self.loop)
                    await msg.edit(content=key + (k * i) + '**')
                await asyncio.sleep(0.97, loop=self.loop)
                await msg.edit(content=mkey + '...:drum:**')
                await asyncio.sleep(0.97, loop=self.loop)
                await msg.edit(content=key + '...:drum: ' + str(winner) + '!**')
                game['players'][winner] += 1
                game['round'] += 1
                game['round_active'] = False
                await asyncio.sleep(1.5, loop=self.loop)
                await ctx.send(f'Leaders: to set the topic for the next round, do `{ctx.prefix}gamenight topic [topic]`!')
            else:
                await ctx.send(ctx.mention + ' That person isn\'t in this game night session!')
        else:
            await ctx.send(ctx.mention + ' There isn\'t a game night session in this channel!')

    @gamenight.command()
    async def join(self, ctx):
        """Join the current channel's game night session.
        Usage: gamenight join"""
        if ctx.channel.id in self.games:
            game = self.games[ctx.channel.id]
            if game['recruiting']:
                if ctx.author in game:
                    await ctx.send(ctx.mention + ' You\'re already in the game night session! **ALLOWING FOR DEV TESTING PURPOSES**')
                    game['players'][ctx.author] = 0
                else:
                    game['players'][ctx.author] = 0
                    await ctx.send(ctx.mention + ' You\'ve joined the game night session!')
            else:
                await ctx.send(ctx.mention + ' It\'s too late to join this game night session!')
        else:
            await ctx.send(ctx.mention + ' There isn\'t a game night session in this channel!')

    @gamenight.command()
    async def start(self, ctx):
        or_check_perms(ctx, ['manage_guild', 'manage_channels', 'manage_messages', 'manage_roles'])
        await ctx.send(f':clap: Use `{ctx.prefix}gamenight memewar [topic]` for now.')

def setup(bot):
    c = GameNight(bot)
    bot.add_cog(c)
