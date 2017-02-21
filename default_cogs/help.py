"""The ever so famous help cog."""
import random
import discord
import util.commands as commands
from util.perms import or_check_perms
from .cog import Cog

class Help(Cog):
    """The essential cog, Help."""

    @commands.command(pass_context=True, aliases=['halp', 'phelp', 'phalp'])
    async def help(self, ctx, *commands_or_cogs: str):
        """Show the bot's help.
        Usage: help"""
        if ctx.invoked_with.startswith('p'):
            or_check_perms(ctx, ['bot_admin', 'manage_server', 'manage_messages', 'manage_channels'])
        try:
            if ctx.message.server.me:
                target = ctx.message.server.me
            else:
                target = self.bot.user
        except AttributeError:
            target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        pages = []
        cog_assign = {}
        fields = {}
        chars = 0
        emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
        emb.title = 'Bot Help'
        emb.set_author(name=target.display_name, icon_url=avatar_link)
        if not commands_or_cogs:
            for name, cmd in self.bot.commands.items():
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
                    for cmd in self.bot.commands.values():
                        if cmd.cog_name == cog_names[litem]:
                            if cmd.name not in did_names:
                                if not cmd.hidden:
                                    field.append('\u2022 **' + cmd.name + '**: *' + (cmd.short_doc if cmd.short_doc else 'I\'m a command.') + '*')
                                    did_names.append(cmd.name)
                    fields[cog_names[litem]] = field
                    item_done = True
                if litem in self.bot.commands:
                    cmd = self.bot.commands[litem]
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
            if chars + pre_len < 6000:
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
                emb = discord.Embed(color=int('0x%06X' % random.randint(0, 256**3-1), 16))
                emb.title = 'Bot Help'
                emb.set_author(name=target.display_name, icon_url=avatar_link)
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
        if not pages:
            pages.append(emb)
        pages[-1].set_footer(icon_url=avatar_link, text='Enjoy!')
        destination = ctx.message.author
        if chars <= 1500:
            destination = ctx.message.channel
        if len(pages) > 1:
            destination = ctx.message.author
        if ctx.invoked_with.startswith('p'):
            destination = ctx.message.channel
        if self.bot.selfbot:
            destination = ctx.message.channel
        for page in pages:
            try:
                await self.bot.send_message(destination, embed=page)
            except discord.HTTPException:
                await self.bot.send_message(destination, 'Error sending embed. Cogs/Commands: ' + ', '.join([f['name'] for f in page.to_dict()['fields']]))
        if destination == ctx.message.author:
            if not ctx.message.channel.is_private:
                await self.bot.say(ctx.message.author.mention + ' **__I\'ve private messaged you my help, please check your DMs!__**')

def setup(bot):
    bot.add_cog(Help(bot))
