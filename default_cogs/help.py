"""The ever so famous help cog."""
import random
import discord
from discord.ext import commands
from util.perms import or_check_perms
from .cog import Cog

class Help(Cog):
    """The essential cog, Help."""
    def __init__(self, bot):
        super().__init__(bot)
        self.char_limit = 3500

    @commands.command(aliases=['halp', 'phelp', 'phalp'])
    async def help(self, ctx, *commands_or_cogs: str):
        """Show the bot's help.
        Usage: help"""
        if ctx.invoked_with.startswith('p'):
            or_check_perms(ctx, ['bot_admin', 'manage_guild', 'manage_messages', 'manage_channels'])
        pages = []
        cog_assign = {}
        fields = {}
        chars = 0
        emb = discord.Embed(color=random.randint(0, 255**3-1))
        emb.title = 'Bot Help'
        emb.set_author(name=ctx.me.display_name, icon_url=ctx.me.avatar_url)
        if not commands_or_cogs:
            for name, cmd in self.bot.all_commands.items():
                if cmd.cog_name:
                    cog = cmd.cog_name
                else:
                    cog = 'No Category'
                if cog not in cog_assign:
                    cog_assign[cog] = []
                cog_assign[cog].append(cmd)
            for group, cmds in cog_assign.items():
                field = []
                did_names = []
                for cmd in cmds:
                    if cmd.name not in did_names:
                        if not cmd.hidden:
                            field.append('\u2022 **' + cmd.name + '**: *' + (cmd.short_doc if cmd.short_doc else 'I\'m a command.') + '*')
                            did_names.append(cmd.name)
                fields[group] = field
        else: # got commands OR cogs here, and don't know which.
            lcogs = {c.lower(): self.bot.cogs[c] for c in self.bot.cogs}
            cog_names = {c.lower(): c for c in self.bot.cogs}
            for item in commands_or_cogs[0:25]:
                litem = item.lower()
                item_done = False
                if litem in lcogs:
                    did_names = []
                    field = []
                    for cmd in self.bot.all_commands.values():
                        if cmd.cog_name == cog_names[litem]:
                            if cmd.name not in did_names:
                                if not cmd.hidden:
                                    field.append('\u2022 **' + cmd.name + '**: *' + (cmd.short_doc if cmd.short_doc else 'I\'m a command.') + '*')
                                    did_names.append(cmd.name)
                    fields[cog_names[litem]] = field
                    item_done = True
                if litem in self.bot.all_commands:
                    cmd = self.bot.all_commands[litem]
                    field = '`' + ctx.prefix
                    if cmd.aliases:
                        field += '[' + cmd.name + '|' + '|'.join(cmd.aliases) + ']`'
                    else:
                        field += cmd.name + '`'
                    field += '\n\n' + (cmd.help if cmd.help else 'I\'m a command.')
                    fields['\u200b' + item] = (field,)
                    item_done = True
                if not item_done:
                    fields['\u200b' + item] = ('No such command or cog.',)
        chars = 0
        for cog in fields:
            field = fields[cog]
            content = '\n'.join(field)
            if not content:
                content = 'No visible commands.'
            pre_len = sum([len(i) for i in field])
            if chars + pre_len < self.char_limit:
                if len(content) <= 1024:
                    emb.add_field(name=cog, value=content)
                else:
                    pager = commands.Paginator(prefix='', suffix='', max_size=1024)
                    for ln in field:
                        pager.add_line(ln)
                    for page in pager.pages:
                        emb.add_field(name=cog, value=page)
            else:
                pages.append(emb)
                emb = discord.Embed(color=random.randint(0, 255**3-1))
                emb.set_author(name=ctx.me.display_name, icon_url=ctx.me.avatar_url)
                chars = 0
                if len(content) <= 1024:
                    emb.add_field(name=cog, value=content)
                else:
                    pager = commands.Paginator(prefix='', suffix='', max_size=1024)
                    for ln in field:
                        pager.add_line(ln)
                    for page in pager.pages:
                        emb.add_field(name=cog, value=page)
            chars += pre_len
        self.logger.info('Generated help, ending with ' + str(chars) + ' chars')
        if not pages:
            pages.append(emb)
        destination = ctx.author
        if chars < 1000:
            destination = ctx.channel
        if len(pages) > 1:
            destination = ctx.author
        if ctx.invoked_with.startswith('p'):
            destination = ctx.channel
        if self.bot.selfbot:
            destination = ctx.channel
        for page in pages:
            try:
                await destination.send(embed=page)
            except discord.HTTPException:
                self.bot._last_help_embeds = pages
                await destination.send('Error sending embed. Cogs/Commands: ' + ', '.join([f['name'] for f in page.to_dict()['fields']]))
        if destination == ctx.author:
            if isinstance(ctx.channel, discord.abc.GuildChannel):
                await ctx.send(ctx.mention + ' **__I\'ve sent you my help, please check your DMs!__**')

def setup(bot):
    bot.add_cog(Help(bot))
