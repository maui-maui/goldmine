"""The bot's Owner module."""
from __future__ import print_function
from importlib import import_module as imp
import distutils.dir_util
import json
import json.decoder
import random
import functools
import io
import copy
import subprocess
import aiohttp
import discord
import os
import shutil
import async_timeout
import sys
import asyncio
import util.commands as commands
from contextlib import suppress
from util.perms import echeck_perms, check_perms
from util.func import bdel, DiscordFuncs, _set_var, _import, _del_var, snowtime, assert_msg, check
import util.dynaimport as di
from .cog import Cog

zipfile = di.load('zipfile')

def gimport(mod_name, name=None, attr=None):
    exec(_import(mod_name, var_name=name, attr_name=attr))
setvar = lambda v, e: exec(_set_var(v, e))
delvar = lambda v: exec(_del_var(v))

class Owner(Cog):
    """Powerful, owner only commands."""

    def __init__(self, bot):
        self.last_broadcasts = {}
        self.dc_funcs = DiscordFuncs(bot)
        super().__init__(bot)
        self.logger = self.logger.getChild('owner')

    @commands.command(pass_context=True, aliases=['rupdate'])
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Usage: update"""
        echeck_perms(ctx, ('bot_owner',))
        restart = not ctx.invoked_with.startswith('r')
        msg = await self.bot.say('Trying to update...')
        r_key = ', now restarting' if restart else ''
        r_not_key = ', not restarting' if restart else ''
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
        echeck_perms(ctx, ('bot_owner',))
        self.bot.store_writer.cancel()
        await self.bot.store.commit()
        if ctx.invoked_with != 'update':
            await self.bot.say('I\'ll try to restart. Hopefully I come back alive :stuck_out_tongue:')
        self.logger.info('The bot is now restarting!')
        self.bot.is_restart = True
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(pass_context=True, aliases=['dwrite'], hidden=True)
    async def dcommit(self, ctx):
        """Commit the current datastore.
        Usage: dcommit"""
        echeck_perms(ctx, ('bot_owner',))
        await self.bot.store.commit()
        await self.bot.say('**Committed the current copy of the datastore!**')

    @commands.command(pass_context=True, hidden=True)
    async def dload(self, ctx):
        """Load the datastore from disk.
        Usage: dload"""
        echeck_perms(ctx, ('bot_owner',))
        await self.bot.say('**ARE YOU SURE YOU WANT TO LOAD THE DATASTORE?** *yes, no*')
        resp = await self.bot.wait_for_message(channel=ctx.message.channel, author=ctx.message.author)
        if resp.content.lower() == 'yes':
            await self.bot.store.read()
            await self.bot.say('**Read the datastore from disk, overwriting current copy!**')
        else:
            await self.bot.say('**Didn\'t say yes, aborting.**')

    @commands.cooldown(1, 16, type=commands.BucketType.default)
    @commands.command(pass_context=True)
    async def broadcast(self, ctx, *, broadcast_text: str):
        """Broadcast a message to all servers.
        Usage: broadcast [message]"""
        echeck_perms(ctx, ('bot_owner',))
        err = ''
        def get_prefix(s):
            props = self.bot.store['properties']
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
        for i in list(self.bot.servers)[:]:
            text = broadcast_text.replace('%prefix%', get_prefix(i))
            if i.id in self.bot.store['nobroadcast']:
                pass
            else:
                try:
                    self.last_broadcasts[i.id] = await self.bot.send_message(i.default_channel, text)
                except discord.Forbidden:
                    satisfied = False
                    c_count = 0
                    try_channels = list(i.channels)[:]
                    channel_count = len(try_channels) - 1
                    while not satisfied:
                        with suppress(discord.Forbidden, discord.HTTPException):
                            self.last_broadcasts[i.id] = await self.bot.send_message(try_channels[c_count], text)
                            satisfied = True
                        if c_count >= channel_count:
                            err += f'`[WARN]` Couldn\'t broadcast to server **{i.name}**\n'
                            satisfied = True
                        c_count += 1
                await asyncio.sleep(0.175)
        if err:
            await self.bot.say(err)

    @commands.command(pass_context=True, hidden=True, aliases=['reval'])
    async def eval(self, ctx, *, code: str):
        """Evaluate some code in command scope.
        Usage: eval [code to execute]"""
        echeck_perms(ctx, ('bot_owner',))
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

    @commands.command(pass_context=True, hidden=True, aliases=['rseval'])
    async def seval(self, ctx, *, code: str):
        """Evaluate some code (multi-statement) in command scope.
        Usage: seval [code to execute]"""
        echeck_perms(ctx, ('bot_owner',))
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
        echeck_perms(ctx, ('bot_admin',))
        try:
            self.bot.store.set_prop(ctx.message, scope, pname, value)
        except Exception:
            await self.bot.say('⚠ An error occured.')
            return
        await self.bot.say('Successfully set `{0}` as `{1}`!'.format(pname, value))

    @commands.command(pass_context=True, hidden=True, aliases=['slist'])
    async def serverlist(self, ctx):
        """List the servers I am in.
        Usage: serverlist"""
        echeck_perms(ctx, ('bot_owner',))
        pager = commands.Paginator()
        for server in self.bot.servers:
            pager.add_line(server.name)
        for page in pager.pages:
            await self.bot.say(page)

    @commands.command(pass_context=True, hidden=True, aliases=['stree'])
    async def servertree(self, ctx, *ids: str):
        """List the servers I am in (tree version).
        Usage: servertree"""
        echeck_perms(ctx, ('bot_owner',))
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

    @commands.command(pass_context=True)
    async def sendfile(self, ctx, path: str = 'assets/soon.gif', msg: str = '📧 File incoming! 📧'):
        """Send a file to Discord.
        Usage: sendfile [file path] {message}"""
        echeck_perms(ctx, ('bot_owner',))
        with open(path, 'rb') as f:
            await self.bot.send_file(ctx.message.channel, fp=f, content=msg)

    @commands.command(pass_context=True)
    async def messages(self, ctx, *number: int):
        """Read contact messages.
        Usage: messages {number}"""
        echeck_perms(ctx, ('bot_owner',))
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
            nums = range(self.bot.store.store.get('msgs_read_index', 0), len(self.bot.store.store['owner_messages']))
        for num in nums:
            msg = self.bot.store.store['owner_messages'][num]
            emb = discord.Embed(color=random.randint(1, 255**3-1))
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

    @commands.command(pass_context=True, aliases=['ccalls', 'cmdcalls', 'commandcalls', 'cmd_calls'])
    async def command_calls(self, ctx):
        """Get the specific command calls.
        Usage: command_calls"""
        echeck_perms(ctx, ('bot_owner',))
        emb = discord.Embed(color=random.randint(1, 255**3-1), title='Command Calls')
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
        echeck_perms(ctx, ('bot_owner',))
        await self.bot.say(':warning: Are you **sure** you want to stop the bot? Type `yes` to continue.')
        if not (await self.bot.wait_for_message(timeout=7.0, author=ctx.message.author,
                                                channel=ctx.message.channel,
                                                check=lambda m: m.content.lower().startswith('yes'))):
            return
        await self.bot.logout()

    @commands.command(pass_context=True)
    async def msg_rate(self, ctx):
        """Get the message rate.
        Usage: msg_rate"""
        echeck_perms(ctx, ('bot_owner',))
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

    @commands.command(pass_context=True, aliases=['edata'])
    async def embed_from_json(self, ctx, *, js_text: str):
        """Send an embed from JSON.
        Usage: embed_from_json [json]"""
        echeck_perms(ctx, ('bot_owner',))
        class SemiEmbed:
            def __init__(self, obj):
                self.obj = obj
            def to_dict(self):
                return self.obj
        try:
            embed_obj = json.loads(js_text)
        except json.decoder.JSONDecodeError:
            await self.bot.say(':warning: **Invalid JSON data!**')
        else:
            sembed = SemiEmbed(embed_obj)
            try:
                await self.bot.say(embed=sembed)
            except discord.HTTPException as e:
                if '400' in str(e):
                    await self.bot.say(':warning: **Couldn\'t send embed, check your data!**')
                else:
                    raise e

def setup(bot):
    c = Owner(bot)
    bot.add_cog(c)
