"""Definition of the bot's Admin module.'"""
from contextlib import suppress
from util.perms import or_check_perms, echeck_perms, check_perms
from util.const import muted_perms
import util.dynaimport as di
from .cog import Cog

for mod in ['asyncio', 'random', 'discord']:
    globals()[mod] = di.load(mod)
commands = di.load('util.commands')

class Admin(Cog):
    """Commands useful for admins and/or moderators.
    Can be extremely powerful, use with caution!
    """

    @commands.command(pass_context=True, aliases=['clear', 'nuke', 'prune', 'clean'], no_pm=True)
    async def purge(self, ctx, *count):
        """Purge a channel of messages.
        Usage: purge"""
        if self.bot.selfbot:
            await self.bot.say('**That command doesn\'t work in selfbot mode, due to a Discord restriction.**')
            return
        await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
        mode = 'count'
        detected = False
        if not count:
            limit = 1500
            detected = True
        elif len(count) == 1:
            if count[0] == 'infinite':
                limit = 1600
                detected = True
            else:
                try:
                    limit = abs(int(count[0])) + 1
                    if limit > 1600:
                        await self.bot.say(ctx.message.author.mention + ' **You can only clean messages by user or 1-1600!**')
                        return
                    detected = True
                except ValueError:
                    pass
        if not detected:
            mode = 'target'
            targets = set()
            members = {}
            s = ctx.message.server
            for i in getattr(s, 'members', []):
                members[i.mention] = i
                members[i.id] = i
                members[i.display_name] = i
                members[i.name] = i
            for i in count:
                try:
                    member = s.get_member(i)
                except AttributeError:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                if member:
                    targets.add(member)
                else:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                    if member:
                        targets.add(member)
            names = []
            _i = 0
            while _i < len(count):
                names.append(count[_i])
                with suppress(KeyError):
                    if ' '.join(names) in members:
                        targets.add(members[' '.join(names)])
                        names = []
                    elif _i + 1 == len(count):
                        targets.add(members[count[0]])
                        _i = -1
                        users = count[1:]
                        names = []
                _i += 1
            if not targets:
                await self.bot.say('**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                return
            purge_ids = [m.id for m in targets]
        try:
            if mode == 'count':
                deleted = await self.bot.purge_from(ctx.message.channel, limit=limit)
            else:
                deleted = await self.bot.purge_from(ctx.message.channel, limit=1500, check=lambda m: m.author.id in purge_ids)
        except discord.Forbidden:
            await self.bot.say(ctx.message.author.mention + ' **I don\'t have enough permissions to do that here 😢**')
            return
        except discord.HTTPException as e:
            if '14 days old' in str(e):
                await self.bot.say('I can only purge messages under 14 days old :sob:')
                return
            else:
                raise e
        dn = len(deleted)
        del_msg = await self.bot.say('👏 I\'ve finished, deleting {0} message{1}!'.format((dn if dn else 'no'), ('' if dn == 1 else 's')))
        await asyncio.sleep(2.8)
        await self.bot.delete_message(del_msg)

    @commands.command(pass_context=True, aliases=['amiadmin', 'isadmin', 'admin'])
    async def admintest(self, ctx):
        """Check to see if you're registered as a bot admin.
        Usage: admintest'"""
        tmp = await check_perms(ctx, ('bot_admin',))
        if tmp:
            await self.bot.say(ctx.message.author.mention + ' You are a bot admin! :smiley:')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin! :slight_frown:')

    @commands.command(pass_context=True, aliases=['adminadd'])
    async def addadmin(self, ctx, *rrtarget: str):
        """Add a user to the bot admin list.
        Usage: addadmin [user]"""
        tmp = await check_perms(ctx, ('bot_admin',))
        if not rrtarget:
            await self.bot.say('**You need to specify a name, nickname, name#0000, mention, or ID!**')
            return
        rtarget = ' '.join(rrtarget)
        try:
            _target = ctx.message.server.get_member_named(rtarget)
        except AttributeError:
            _target = None
        if _target:
            target = _target.id
        elif len(rtarget) == 18:
            target = rrtarget[0]
        elif ctx.message.mentions:
            target = ctx.message.mentions[0].id
        else:
            await self.bot.say('**Invalid name! Name, nickname, name#0000, mention, or ID work.**')
            return
        if tmp:
            aentry = target
            if aentry not in self.dstore['bot_admins']:
                self.dstore['bot_admins'].append(aentry)
                await self.bot.say('The user specified has successfully been added to the bot admin list!')
            else:
                await self.bot.say('The user specified is already a bot admin!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not add others as admins!')

    @commands.command(pass_context=True, aliases=['deladmin', 'admindel', 'adminrm'])
    async def rmadmin(self, ctx, *rrtarget: str):
        """Remove a user from the bot admin list.
        Usage: rmadmin [user]"""
        tmp = await check_perms(ctx, ('bot_admin',))
        if not rrtarget:
            await self.bot.say('**You need to specify a name, nickname, name#discriminator, or ID!**')
            return
        rtarget = ' '.join(rrtarget)
        try:
            _target = ctx.message.server.get_member_named(rtarget)
        except AttributeError:
            _target = None
        if _target:
            target = _target.id
        elif len(rtarget) in [15, 16, 17, 18, 19, 20]:
            target = rrtarget[0]
        else:
            await self.bot.say('**Invalid name! Name, nickname, name#discriminator, or ID work.**')
            return
        if tmp:
            aentry = target
            try:
                self.dstore['bot_admins'].remove(aentry)
            except ValueError:
                await self.bot.say('The user specified is not a bot admin!')
            else:
                await self.bot.say('The user specified has successfully been demoted!')
        else:
            await self.bot.say(ctx.message.author.mention + ' You are not a bot admin, so you may not demote other admins!')

    @commands.command(pass_context=True, aliases=['admins'])
    async def adminlist(self, ctx):
        """List all bot admins defined.
        Usage: adminlist"""
        alist = ''
        for i in self.dstore['bot_admins']:
            nid = ''
            try:
                _name = ctx.message.server.get_member(i)
            except AttributeError:
                _name = None
            if not _name:
                try:
                    _name = await self.bot.get_user_info(i)
                except discord.NotFound:
                    _name = 'UNKNOWN'
                    nid = i
            if not nid:
                nid = _name.id
            alist += '**' + str(_name) + f'** (ID `{nid}`)\n'
        await self.bot.say('The following people are bot admins:\n' + alist)

    @commands.command(pass_context=True)
    async def getprop(self, ctx, pname: str):
        """Fetch a property from the datastore.
        Usage: getprop [property name]"""
        try:
            pout = self.store.get_prop(ctx.message, pname)
        except Exception:
            await self.bot.say('⚠ An error occured.')
            return
        await self.bot.say(pout)

    @commands.command(pass_context=True, no_pm=True)
    async def setprop(self, ctx, pname: str, *, value: str):
        """Set the value of a property on server level.
        Usage: setprop [property name] [value]"""
        await echeck_perms(ctx, ('manage_server',))
        self.store.set_prop(ctx.message, 'by_server', pname, value)
        await self.bot.say(':white_check_mark:')

    @commands.command(pass_context=True, aliases=['getprefix', 'setprefix'])
    async def prefix(self, ctx, *prefix: str):
        """Get or set the command prefix.
        Usage: prefix {new prefix}"""
        sk = ' server'
        prop = ('by_server', 'command_prefix')
        if self.bot.selfbot:
            sk = ''
            prop = ('global', 'selfbot_prefix')
        if prefix:
            await or_check_perms(ctx, ['manage_server', 'manage_channels', 'manage_messages'])
            jprefix = ' '.join(prefix)
            self.store.set_prop(ctx.message, *prop, jprefix)
            await self.bot.say(':white_check_mark:')
        else:
            oprefix = self.store.get_cmdfix(ctx.message)
            await self.bot.say('**Current%s command prefix is: **`%s`' % (sk, oprefix))

    async def progress(self, msg: discord.Message, begin_txt: str):
        """Play loading animation with dots and moon."""
        fmt = '{0}{1} {2}'
        anim = '🌑🌒🌓🌔🌕🌝🌖🌗🌘🌚'
        anim_len = len(anim) - 1
        anim_i = 0
        dot_i = 1
        while True:
            await self.bot.edit_message(msg, fmt.format(begin_txt, ('.' * dot_i) + ' ' * (3 - dot_i), anim[anim_i]))
            dot_i += 1
            if dot_i > 3:
                dot_i = 1
            anim_i += 1
            if anim_i > anim_len:
                anim_i = 0
            await asyncio.sleep(1.1)

    @commands.command(pass_context=True, no_pm=True)
    async def mute(self, ctx, *, member: discord.Member):
        """Mute someone on voice and text chat.
        Usage: mute [person's name]"""
        await or_check_perms(ctx, ['mute_members', 'manage_roles', 'manage_channels', 'manage_messages'])
        status = await self.bot.say('Muting... 🌚')
        pg_task = self.loop.create_task(asyncio.wait_for(self.progress(status, 'Muting'), timeout=30, loop=self.loop))
        try:
            ch_perms = discord.PermissionOverwrite(**{p: False for p in muted_perms})
            for channel in ctx.message.server.channels:
                await self.bot.edit_channel_permissions(channel, member, ch_perms)
            await self.bot.server_voice_state(member, mute=True, deafen=None)
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('Successfully muted **%s**!' % str(member))
        except (discord.Forbidden, discord.HTTPException):
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('**I don\'t have enough permissions to do that!**')

    @commands.command(pass_context=True, no_pm=True)
    async def unmute(self, ctx, *, member: discord.Member):
        """Unmute someone on voice and text chat.
        Usage: unmute [person's name]"""
        await or_check_perms(ctx, ('mute_members', 'manage_roles', 'manage_channels', 'manage_messages'))
        status = await self.bot.say('Unmuting... 🌚')
        pg_task = self.loop.create_task(asyncio.wait_for(self.progress(status, 'Unmuting'), timeout=30, loop=self.loop))
        role_map = {r.name: r for r in member.roles}
        try:
            if 'Muted' in role_map:
                await self.bot.remove_roles(member, role_map['Muted'])
            ch_perms = discord.PermissionOverwrite(**{p: None for p in muted_perms})
            for channel in ctx.message.server.channels:
                await self.bot.edit_channel_permissions(channel, member, ch_perms)
            await self.bot.server_voice_state(member, mute=False, deafen=None)
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('Successfully unmuted **%s**!' % str(member))
        except (discord.Forbidden, discord.HTTPException):
            pg_task.cancel()
            await self.bot.delete_message(status)
            await self.bot.say('**I don\'t have enough permissions to do that!**')

    @commands.command(pass_context=True, no_pm=True)
    async def ban(self, ctx, *, member: discord.Member):
        """Ban someone from the server.
        Usage: ban [member]"""
        await echeck_perms(ctx, ('ban_members',))
        await self.bot.say(':hammer: **Are you sure you want to ban ' + member.mention + '?**')
        if not (await self.bot.wait_for_message(timeout=6.0, author=ctx.message.author,
                                                channel=ctx.message.channel,
                                                check=lambda m: m.content.lower().startswith('y'))):
            await self.bot.say('Not banning.')
            return
        await self.bot.ban(member)
        await self.bot.say(':hammer: Banned. It was just about time.')

def setup(bot):
    c = Admin(bot)
    bot.add_cog(c)
