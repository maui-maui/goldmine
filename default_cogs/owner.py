"""The bot's Owner module."""
from __future__ import print_function
from importlib import import_module as imp
import distutils.dir_util
from contextlib import suppress
from util.perms import echeck_perms, check_perms
from util.func import bdel, DiscordFuncs, _set_var, _import, _del_var, snowtime, assert_msg, check
import util.dynaimport as di
from .cog import Cog

for mod in ['random', 'functools', 'zipfile', 'io', 'copy', 'subprocess',
            'aiohttp', 'async_timeout', 'discord', 'os', 'shutil', 'sys']:
    globals()[mod] = di.load(mod)
commands = di.load('util.commands')

def gimport(mod_name, name=None, attr=None):
    return exec(_import(mod_name, var_name=name, attr_name=attr))
setvar = lambda v, e: exec(_set_var(v, e))
delvar = lambda v: exec(_del_var(v))

class Owner(Cog):
    """Powerful, owner only commands."""

    def __init__(self, bot):
        self.last_broadcasts = {}
        self.dc_funcs = DiscordFuncs(bot)
        super().__init__(bot)

    @commands.command(pass_context=True, aliases=['rawupdate', 'rupdate'])
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Usage: update"""
        await echeck_perms(ctx, ('bot_owner',))
        restart = not ctx.invoked_with.startswith('r')
        msg = await self.bot.say('Trying to update...')
        r_key = ', now restarting' if restart else ''
        r_not_key = ', not restarting' if restart else ''
#        subprocess.check_output(['git', 'reset', 'HEAD', '--hard'])
        dest = ctx.message.channel if self.bot.selfbot else ctx.message.author
        try:
            gitout = await self.loop.run_in_executor(None, functools.partial(subprocess.check_output, ['git', 'pull'], stderr=subprocess.STDOUT))
            gitout = gitout.decode('utf-8')
        except (subprocess.CalledProcessError, FileNotFoundError) as exp:
            if ('status 128' in str(exp)) or isinstance(exp, FileNotFoundError):
                async with aiohttp.ClientSession() as session:
                    with async_timeout.timeout(16): # for streaming
                        async with session.get('https://github.com/Armored-Dragon/goldmine/archive/master.zip') as r:
                            tarball = await r.read()
                with zipfile.ZipFile(io.BytesIO(tarball)) as z:
                    z.extractall(os.path.join(self.bot.dir, 'data'))
                distutils.dir_util.copy_tree(os.path.join(self.bot.dir, 'data', 'goldmine-master'), self.bot.dir)
                shutil.rmtree(os.path.join(self.bot.dir, 'data', 'goldmine-master'))
                gitout = 'Successfully updated via zip.\nZip size: ' + str(sys.getsizeof(tarball) / 1048576) + ' MB'
            else:
                await self.bot.edit_message(msg, 'An error occured while attempting to update!')
                await self.bot.send_message(dest, '```' + str(exp) + '```')
                gitout = False
        if gitout != False:
            await self.bot.send_message(dest, 'Update Output:\n```' + gitout + '```')
        if not gitout:
            await self.bot.edit_message(msg, msg.content + f'\nUpdate failed{r_not_key}.')
        elif gitout.split('\n')[-2:][0] == 'Already up-to-date.':
            await self.bot.edit_message(msg, f'Bot was already up-to-date{r_not_key}.')
        else:
            await self.bot.edit_message(msg, f'Bot was able to update{r_key}.')
        if restart:
            await self.restart.invoke(ctx)

    @commands.command(pass_context=True)
    async def restart(self, ctx):
        """Restarts this bot.
        Usage: restart"""
        await echeck_perms(ctx, ('bot_owner',))
#        for i in self.bot.servers:
#            await self.bot.send_message(i.default_channel, 'This bot (' + self.bname + ') is now restarting!')
        self.bot.store_writer.cancel()
        await self.store.commit()
        if ctx.invoked_with != 'update':
            await self.bot.say('I\'ll try to restart. Hopefully I come back alive :stuck_out_tongue:')
        self.logger.info('The bot is now restarting!')
        self.bot.is_restart = True
        os.execl(sys.executable, sys.executable, *sys.argv)
#        await self.bot.logout() # Comment for people to not see that the bot restarted (to trick uptime)
#        self.loop.call_soon_threadsafe(self.loop.stop)

    @commands.command(pass_context=True, aliases=['dwrite', 'storecommit', 'commitstore', 'commit_store', 'write_store'], hidden=True)
    async def dcommit(self, ctx):
        """Commit the current datastore.
        Usage: dcommit"""
        await echeck_perms(ctx, ('bot_owner',))
        await self.store.commit()
        await self.bot.say('**Commited the current copy of the datastore!**')

    @commands.command(pass_context=True, aliases=['dread', 'storeread', 'readstore', 'load_store', 'read_store'], hidden=True)
    async def dload(self, ctx):
        """Load the datastore from disk.
        Usage: dload"""
        await echeck_perms(ctx, ('bot_owner',))
        await self.bot.say('**ARE YOU SURE YOU WANT TO LOAD THE DATASTORE?** *yes, no*')
        resp = await self.bot.wait_for_message(channel=ctx.message.channel, author=ctx.message.author)
        if resp.content.lower() == 'yes':
            await self.store.read()
            await self.bot.say('**Read the datastore from disk, overwriting current copy!**')
        else:
            await self.bot.say('**Didn\'t say yes, aborting.**')

    @commands.cooldown(1, 16, type=commands.BucketType.default)
    @commands.command(pass_context=True)
    async def broadcast(self, ctx, *, broadcast_text: str):
        """Broadcast a message to all servers.
        Usage: broadcast [message]"""
        await echeck_perms(ctx, ('bot_owner',))
        err = ''
        def get_prefix(s):
            props = self.dstore['properties']
            servs = props['by_server']
            if s.id in servs:
                if 'command_prefix' in servs[s.id]:
                    return servs[s.id]['command_prefix']
                else:
                    return props['global']['command_prefix']
            else:
                return props['global']['command_prefix']
        if self.bot.selfbot:
            await self.bot.say(''':warning: **This could potentially get you banned with a selfbot.**
If you're sure you want to do this, type `yes` within 8 seconds.''')
            if not (await self.bot.wait_for_message(timeout=8.0, author=ctx.message.author,
                                                channel=ctx.message.channel,
                                                check=lambda m: m.content.lower().startswith('yes'))):
                return
        for i in self.bot.servers:
            text = broadcast_text.replace('%prefix%', get_prefix(i))
            if i.id in self.dstore['nobroadcast']:
                pass
            else:
                try:
                    self.last_broadcasts[i.id] = await self.bot.send_message(i.default_channel, text)
                except discord.Forbidden:
                    satisfied = False
                    c_count = 0
                    try_channels = list(i.channels)
                    channel_count = len(try_channels) - 1
                    while not satisfied:
                        with suppress(discord.Forbidden, discord.HTTPException):
                            self.last_broadcasts[i.id] = await self.bot.send_message(try_channels[c_count], text)
                            satisfied = True
                        if c_count >= channel_count:
                            err += f'`[WARN]` Couldn\'t broadcast to server **{i.name}**\n'
                            satisfied = True
                        c_count += 1
        if err:
            await self.bot.say(err)

    @commands.command(pass_context=True, hidden=True, aliases=['pyeval', 'rxeval', 'reref', 'xeval'])
    async def eref(self, ctx, *, code: str):
        """Evaluate some code in command scope.
        Usage: eref [code to execute]"""
        await echeck_perms(ctx, ('bot_owner',))
        dc = self.dc_funcs
        def print(*ina: str):
            self.loop.create_task(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = eval(bdel(bdel(code, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ev_output is None:
            await self.bot.say('✅')
            return
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')
    @commands.command(pass_context=True, hidden=True, aliases=['rseref', 'meref', 'rmeref'])
    async def seref(self, ctx, *, code: str):
        """Evaluate some code (multi-statement) in command scope.
        Usage: seref [code to execute]"""
        await echeck_perms(ctx, ('bot_owner',))
        dc = self.dc_funcs
        def print(*ina: str):
            self.loop.create_task(self.bot.say(' '.join(ina)))
            return True
        try:
            ev_output = exec(bdel(bdel(code, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ev_output is None:
            await self.bot.say('✅')
            return
        if ctx.invoked_with.startswith('r'):
            await self.bot.say(o)
        else:
            await self.bot.say('```py\n' + o + '```')

    @commands.command(pass_context=True, aliases=['rsetprop'])
    async def rawsetprop(self, ctx, scope: str, pname: str, value: str):
        """Set the value of a property on any level.
        Usage: rawsetprop [scope] [property name] [value]"""
        await echeck_perms(ctx, ('bot_admin',))
        try:
            self.store.set_prop(ctx.message, scope, pname, value)
        except Exception:
            await self.bot.say('⚠ An error occured.')
            return
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))

    @commands.command(pass_context=True)
    async def suspend(self, ctx):
        """Bring the bot offline (in a resumable state).
        Usage: suspend'"""
        await echeck_perms(ctx, ('bot_owner',))
        await self.bot.suspend()
        await self.bot.say('Successfully **suspended** me! (I should now be offline.)\nI will still count experience points.')
    @commands.command(pass_context=True, aliases=['ssuspend'])
    async def ususpend(self, ctx):
        """Temporarily suspend the bot's command and conversation features.
        Usage: suspend'"""
        await echeck_perms(ctx, ('bot_owner',))
        self.bot.status = 'invisible'
        await self.bot.say('Successfully **suspended** my message processing! (I should stay online.)\nI will still count experience points.')

    @commands.command(pass_context=True, hidden=True, aliases=['slist'])
    async def serverlist(self, ctx):
        """List the servers I am in.
        Usage: serverlist"""
        await echeck_perms(ctx, ('bot_owner',))
        pager = commands.Paginator()
        for server in self.bot.servers:
            pager.add_line(server.name)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['treelist', 'stree', 'treeservers', 'trees', 'tservers'])
    async def servertree(self, ctx, *ids: str):
        """List the servers I am in (tree version).
        Usage: servertree"""
        await echeck_perms(ctx, ('bot_owner',))
        pager = commands.Paginator(prefix='```diff')
        servers: List[discord.Server]
        if ids:
            s_map = {i.id: i for i in self.bot.servers}
            for sid in ids:
                with assert_msg(ctx, '**ID** `%s` **is invalid. (must be 18 numbers)**' % sid):
                    check(len(sid) == 18)
                try:
                    servers.append(s_map[sid])
                except KeyError:
                    await self.bot.say('Server ID **%s** not found.' % sid)
                    return False
        else:
            servers = self.bot.servers
        for server in servers:
            pager.add_line('+ ' + server.name + ' [{0} members] [ID {1}]'.format(str(len(server.members)), server.id))
            for channel in server.channels:
                xname = channel.name
                if str(channel.type) == 'voice':
                    xname = '[voice] ' + xname
                pager.add_line('  • ' + xname)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['mlist', 'listmembers'])
    async def memberlist(self, ctx, *server_ids: str):
        """List the members of a server.
        Usage: memberlist [server ids]"""
        await echeck_perms(ctx, ('bot_owner',))
        if not server_ids:
            await self.bot.say('**You need to specify at least 1 server ID!**')
            return False
        pager = commands.Paginator(prefix='```diff')
        pager.add_line('< -- SERVERS <-> MEMBERS -- >')
        server_table = {i.id: i for i in self.bot.servers}
        for sid in server_ids:
            with assert_msg(ctx, f'**ID** `{sid}` **is invalid. (must be 18 numbers)**'):
                check(len(sid) == 18)
            try:
                server = server_table[sid]
            except KeyError:
                await self.bot.say(f'**ID** `{sid}` **was not found.**')
                return False
            pager.add_line('+ ' + server.name + ' [{0} members] [ID {1}]'.format(str(len(server.members)), server.id))
            for member in server.members:
                pager.add_line('- ' + str(member))
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, aliases=['sf', 'sendf', 'filesend', 'fs'])
    async def sendfile(self, ctx, path: str = 'assets/soon.gif', msg: str = '📧 File incoming! 📧'):
        """Send a file to Discord.
        Usage: sendfile [file path] {message}"""
        await echeck_perms(ctx, ('bot_owner',))
        with open(path, 'rb') as f:
            await self.bot.send_file(ctx.message.channel, fp=f, content=msg)

    @commands.command(pass_context=True, hidden=True)
    async def repeat(self, ctx, times : int, *, command: str):
        """Repeats a command a specified number of times.
        Usage: repeat [times] [command]"""
        await echeck_perms(ctx, ('bot_admin',))
        msg = copy.copy(ctx.message)
        msg.content = command
        for i in range(times):
            await self.bot.process_commands(msg, ctx.prefix)

    @commands.command(pass_context=True)
    async def console_msg(self, ctx):
        """Allow you to type here in the console.
        Usage: console_msg"""
        await echeck_perms(ctx, ('bot_owner',))
        def console_task(ch):
            while True:
                text_in = input('Message> ')
                if text_in == 'quit':
                    return
                else:
                    self.loop.create_task(self.bot.send_message(ch, text_in))
        await self.bot.say('Now entering: Console message mode')
        print('Type \'quit\' to exit.')
        await self.loop.run_in_executor(None, console_task, ctx.message.channel)
        await self.bot.say('Exited console message mode')

    @commands.command(pass_context=True)
    async def messages(self, ctx, *number: int):
        """Read contact messages.
        Usage: messages {number}"""
        await echeck_perms(ctx, ('bot_owner',))
        def chan(msg):
            if 'server' in msg:
                try:
                    server = {s.id: s for s in self.bot.servers}[msg['server_id']]
                except KeyError:
                    return 'server-removed'
                try:
                    channel = {c.id: c for c in server.channels}[msg['channel_id']].name
                except KeyError:
                    return 'deleted-channel'
                msg['channel'] = channel
                return channel
            else:
                return 'was-pm'
        if number:
            nums = number
        else:
            nums = range(self.dstore.get('msgs_read_index', 0), len(self.bot.store.store['owner_messages']))
        for num in nums:
            msg = self.bot.store.store['owner_messages'][num]
            emb = discord.Embed(color=int('0x%06X' % random.randint(1, 255**3-1), 16))
            author = await self.bot.get_user_info(msg['user_id'])
            emb.set_author(name=str(author), icon_url=(author.avatar_url if author.avatar_url else author.default_avatar_url))
            emb.description = msg['message']
            emb.add_field(name='User Tag', value=msg['user'])
            emb.add_field(name='Nickname', value=msg['nick'])
            emb.add_field(name='Message ID', value=msg['message_id'])
            emb.add_field(name='User ID', value=msg['user_id'])
            emb.add_field(name='Channel', value='#' + chan(msg) + '\nID: `' + msg['channel_id'] + '`')
            emb.add_field(name='PM?', value=('Yes' if msg['pm'] else 'No'))
            emb.add_field(name='Date and Time', value=msg['time'])
            emb.add_field(name='Timestamp', value=msg['timestamp'])
            emb.add_field(name='Contains Mention?', value=('Yes' if msg['contains_mention'] else 'No'))
            if 'server' in msg:
                emb.add_field(name='Server', value='**' + msg['server'] + '**\nID: `' + msg['server_id'] +
                                                '`\nMembers at the time: ' + str(msg['server_members']) +
                                                '\nMembers now: ' + str(len({s.id: s for s in self.bot.servers}[msg['server_id']].members)))
            await self.bot.say(embed=emb)
        self.bot.store.store['msgs_read_index'] = nums[-1]
        await self.bot.say('Finished!')
    
    @commands.command(pass_context=True, aliases=['events', 'ecalls', 'evcalls', 'eventcalls', 'ev_calls'])
    async def event_calls(self, ctx):
        """Get the specific event calls.
        Usage: event_calls"""
        await echeck_perms(ctx, ('bot_owner',))
        emb = discord.Embed(color=int('0x%06X' % random.randint(1, 255**3-1), 16), title='Event Calls')
        emb.description = 'Here are all the event calls made.'
        author = self.bot.user
        emb.set_author(name=str(author), icon_url=(author.avatar_url if author.avatar_url else author.default_avatar_url))
        emb.add_field(name='Total', value=sum(self.bot.event_calls.values()))
        for ev, count in reversed(sorted(self.bot.event_calls.items(), key=lambda i: i[1])):
            emb.add_field(name=ev, value=count)
        await self.bot.say(embed=emb)

    @commands.command(pass_context=True, aliases=['ccalls', 'cmdcalls', 'commandcalls', 'cmd_calls'])
    async def command_calls(self, ctx):
        """Get the specific command calls.
        Usage: command_calls"""
        await echeck_perms(ctx, ('bot_owner',))
        emb = discord.Embed(color=int('0x%06X' % random.randint(1, 255**3-1), 16), title='Command Calls')
        emb.description = 'Here are all the command calls made.'
        author = self.bot.user
        emb.set_author(name=str(author), icon_url=(author.avatar_url if author.avatar_url else author.default_avatar_url))
        emb.add_field(name='Total', value=sum(self.bot.command_calls.values()))
        for cmd, count in reversed(sorted(self.bot.command_calls.items(), key=lambda i: i[1])):
            emb.add_field(name=cmd, value=count)
        await self.bot.say(embed=emb)

    @commands.command(pass_context=True)
    async def shutdown(self, ctx):
        """Shut down and stop the bot.
        Usage: shutdown"""
        await echeck_perms(ctx, ('bot_owner',))
        await self.bot.say(':warning: Are you **sure** you want to stop the bot? Type `yes` to continue.')
        if not (await self.bot.wait_for_message(timeout=7.0, author=ctx.message.author,
                                                channel=ctx.message.channel,
                                                check=lambda m: m.content.lower().startswith('yes'))):
            return
        await self.bot.logout()

def setup(bot):
    c = Owner(bot)
    bot.add_cog(c)
