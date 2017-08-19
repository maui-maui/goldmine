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
from discord.ext import commands
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

    @commands.command(aliases=['rupdate'])
    async def update(self, ctx):
        """Auto-updates this bot and restarts if any code was updated.
        Usage: update"""
        echeck_perms(ctx, ('bot_owner',))
        restart = not ctx.invoked_with.startswith('r')
        msg = await ctx.send('Trying to update...')
        r_key = ', now restarting' if restart else ''
        r_not_key = ', not restarting' if restart else ''
        dest = ctx.channel if self.bot.selfbot else ctx.author
        try:
            gitout = await self.loop.run_in_executor(None, functools.partial(subprocess.check_output, ['git', 'pull'], stderr=subprocess.STDOUT))
            gitout = gitout.decode('utf-8')
        except (subprocess.CalledProcessError, FileNotFoundError) as exp:
            if ('status 128' in str(exp)) or isinstance(exp, FileNotFoundError):
                with async_timeout.timeout(25): # for streaming
                    async with self.bot.cog_http.get('https://github.com/Armored-Dragon/goldmine/archive/master.zip') as r:
                        tarball = await r.read()
                with zipfile.ZipFile(io.BytesIO(tarball)) as z:
                    z.extractall(os.path.join(self.bot.dir, 'data'))
                distutils.dir_util.copy_tree(os.path.join(self.bot.dir, 'data', 'goldmine-master'), self.bot.dir)
                shutil.rmtree(os.path.join(self.bot.dir, 'data', 'goldmine-master'))
                gitout = 'Successfully updated via zip.\nZip size: ' + str(sys.getsizeof(tarball) / 1048576) + ' MB'
            else:
                await msg.edit(content='An error occured while attempting to update!')
                await dest.send('```' + str(exp) + '```')
                gitout = False
        if gitout != False:
            await dest.send('Update Output:\n```' + gitout + '```')
        if not gitout:
            await msg.edit(content=msg.content + f'\nUpdate failed{r_not_key}.')
        elif gitout.split('\n')[-2:][0] == 'Already up-to-date.':
            await msg.edit(content=f'Bot was already up-to-date{r_not_key}.')
        else:
            await msg.edit(content=f'Bot was able to update{r_key}.')
        if restart:
            await self.restart.invoke(ctx)

    @commands.command()
    async def restart(self, ctx):
        """Restarts this bot.
        Usage: restart"""
        echeck_perms(ctx, ('bot_owner',))
        self.bot.store_writer.cancel()
        await self.bot.store.commit()
        if ctx.invoked_with != 'update':
            await ctx.send('I\'ll try to restart. Hopefully I come back alive :stuck_out_tongue:')
        self.logger.info('The bot is now restarting!')
        # self.bot.is_restart = True
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(aliases=['dwrite'], hidden=True)
    async def dcommit(self, ctx):
        """Commit the current datastore.
        Usage: dcommit"""
        echeck_perms(ctx, ('bot_owner',))
        self.bot.store.commit()
        await ctx.send('**Committed the current copy of the datastore!**')

    @commands.command(hidden=True)
    async def dload(self, ctx):
        """Load the datastore from disk.
        Usage: dload"""
        echeck_perms(ctx, ('bot_owner',))
        await ctx.send('**ARE YOU SURE YOU WANT TO LOAD THE DATASTORE?** *yes, no*')
        resp = await self.bot.wait_for('message', timeout=15, check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
        if resp.content.lower() == 'yes':
            self.bot.store.read()
            await ctx.send('**Read the datastore from disk, overwriting current copy!**')
        else:
            await ctx.send('**Didn\'t say yes, aborting.**')

    @commands.cooldown(1, 16, type=commands.BucketType.default)
    @commands.command()
    async def broadcast(self, ctx, *, broadcast_text: str):
        """Broadcast a message to all guilds.
        Usage: broadcast [message]"""
        echeck_perms(ctx, ('bot_owner',))
        err = ''
        def get_prefix(s):
            props = self.bot.store['properties']
            servs = props['by_guild']
            if s.id in servs:
                if 'command_prefix' in servs[s.id]:
                    return servs[s.id]['command_prefix']
                else:
                    return props['global']['command_prefix']
            else:
                return props['global']['command_prefix']
        if self.bot.selfbot:
            await ctx.send(''':warning: **This could potentially get you banned with a selfbot.**
If you're sure you want to do this, type `yes` within 8 seconds.''')
            if not (await self.bot.wait_for('message', timeout=8.0,
                                                check=lambda m: m.content.lower().startswith('yes') and m.author == ctx.author and m.channel == ctx.channel)):
                return
        for i in self.bot.guilds:
            text = broadcast_text.replace('%prefix%', get_prefix(i))
            if i.id in self.bot.store['nobroadcast']:
                pass
            else:
                try:
                    self.last_broadcasts[i.id] = await i.default_channel.send(text)
                except discord.Forbidden:
                    satisfied = False
                    c_count = 0
                    try_channels = i.channels
                    channel_count = len(try_channels) - 1
                    while not satisfied:
                        with suppress(discord.Forbidden, discord.HTTPException):
                            self.last_broadcasts[i.id] = await try_channels[c_count].send(text)
                            satisfied = True
                        if c_count >= channel_count:
                            err += f'`[WARN]` Couldn\'t broadcast to guild **{i.name}**\n'
                            satisfied = True
                        c_count += 1
                await asyncio.sleep(0.175)
        if err:
            await ctx.send(err)

    @commands.command(hidden=True, aliases=['reval'])
    async def eval(self, ctx, *, code: str):
        """Evaluate some code in command scope.
        Usage: eval [code to execute]"""
        echeck_perms(ctx, ('bot_owner',))
        dc = self.dc_funcs
        def print(*ina: str):
            self.loop.create_task(ctx.send(' '.join(ina)))
            return True
        try:
            ev_output = eval(bdel(bdel(code, '```python'), '```py').strip('`'))
        except Exception as e:
            ev_output = 'An exception of type %s occured!\n' % type(e).__name__ + str(e)
        o = str(ev_output)
        if ev_output is None:
            await ctx.send('✅')
            return
        if ctx.invoked_with.startswith('r'):
            await ctx.send(o)
        else:
            await ctx.send('```py\n' + o + '```')

    @commands.command(aliases=['rsetprop'])
    async def rawsetprop(self, ctx, scope: str, pname: str, value: str):
        """Set the value of a property on any level.
        Usage: rawsetprop [scope] [property name] [value]"""
        echeck_perms(ctx, ('bot_admin',))
        try:
            self.bot.store.set_prop(ctx.message, scope, pname, value)
        except Exception:
            await ctx.send('⚠ An error occured.')
            return
        await ctx.send('Successfully set `{0}` as `{1}`!'.format(pname, value))

    @commands.command(hidden=True, aliases=['slist', 'serverlist'])
    async def guildlist(self, ctx):
        """List the guilds I am in.
        Usage: guildlist"""
        echeck_perms(ctx, ('bot_owner',))
        pager = commands.Paginator()
        for guild in self.bot.guilds:
            pager.add_line(guild.name)
        for page in pager.pages:
            await ctx.send(page)

    @commands.command(hidden=True, aliases=['stree', 'servertree'])
    async def guildtree(self, ctx, *ids: str):
        """List the guilds I am in (tree version).
        Usage: guildtree"""
        echeck_perms(ctx, ('bot_owner',))
        pager = commands.Paginator(prefix='```diff')
        guilds: List[discord.Guild]
        if ids:
            s_map = {i.id: i for i in self.bot.guilds}
            for sid in ids:
                with assert_msg(ctx, '**ID** `%s` **is invalid. (must be 18 numbers)**' % sid):
                    check(len(sid) == 18)
                try:
                    guilds.append(s_map[sid])
                except KeyError:
                    await ctx.send('guild ID **%s** not found.' % sid)
                    return False
        else:
            guilds = self.bot.guilds
        for guild in guilds:
            pager.add_line('+ ' + guild.name + ' [{0} members] [ID {1}]'.format(str(len(guild.members)), guild.id))
            for channel in guild.channels:
                xname = channel.name
                if str(channel.type) == 'voice':
                    xname = '[voice] ' + xname
                pager.add_line('  • ' + xname)
        for page in pager.pages:
            await ctx.send(page)

    @commands.command()
    async def sendfile(self, ctx, path: str = 'assets/soon.gif', msg: str = '📧 File incoming!'):
        """Send a file to Discord.
        Usage: sendfile [file path] {message}"""
        echeck_perms(ctx, ('bot_owner',))
        await ctx.send(msg, file=discord.File(path))

    @commands.command()
    async def messages(self, ctx, *number: int):
        """Read contact messages.
        Usage: messages {number}"""
        echeck_perms(ctx, ('bot_owner',))
        def chan(msg):
            if 'guild' in msg:
                try:
                    guild = {s.id: s for s in self.bot.guilds}[msg['guild_id']]
                except KeyError:
                    return 'guild-removed'
                try:
                    channel = {c.id: c for c in guild.channels}[msg['channel_id']].name
                except KeyError:
                    return 'deleted-channel'
                msg['channel'] = channel
                return channel
            else:
                return 'was-pm'
        if number:
            nums = number
        else:
            nums = range(self.bot.store.get('msgs_read_index', 0), len(self.bot.store['owner_messages']))
        for num in nums:
            msg = self.bot.store['owner_messages'][num]
            emb = discord.Embed(color=random.randint(1, 255**3-1))
            author = await self.bot.get_user_info(msg['user_id'])
            emb.set_author(name=str(author), icon_url=author.avatar_url)
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
            if 'guild' in msg:
                emb.add_field(name='guild', value='**' + msg['guild'] + '**\nID: `' + msg['guild_id'] +
                                                '`\nMembers at the time: ' + str(msg['guild_members']) +
                                                '\nMembers now: ' + str(len({s.id: s for s in self.bot.guilds}[msg['guild_id']].members)))
            await ctx.send(embed=emb)
        self.bot.store['msgs_read_index'] = nums[-1]
        await ctx.send('Finished!')

    @commands.command(aliases=['ccalls', 'cmdcalls', 'commandcalls', 'cmd_calls'])
    async def command_calls(self, ctx):
        """Get the specific command calls.
        Usage: command_calls"""
        echeck_perms(ctx, ('bot_owner',))
        emb = discord.Embed(color=random.randint(1, 255**3-1), title='Command Calls')
        emb.description = 'Here are all the command calls made.'
        emb.set_author(name=ctx.me.display_name, icon_url=ctx.me.avatar_url)
        emb.add_field(name='Total', value=sum(self.bot.command_calls.values()))
        for cmd, count in reversed(sorted(self.bot.command_calls.items(), key=lambda i: i[1])):
            emb.add_field(name=cmd, value=count)
        await ctx.send(embed=emb)

    @commands.command()
    async def shutdown(self, ctx):
        """Shut down and stop the bot.
        Usage: shutdown"""
        echeck_perms(ctx, ('bot_owner',))
        await ctx.send(':warning: Are you **sure** you want to stop the bot? Type `yes` to continue.')
        if not (await self.bot.wait_for('message', timeout=7.0,
                                                check=lambda m: m.content.lower().startswith('yes') and m.author == ctx.author and m.channel == ctx.channel)):
            return
        await self.bot.logout()

    @commands.command()
    async def msg_rate(self, ctx):
        """Get the message rate.
        Usage: msg_rate"""
        echeck_perms(ctx, ('bot_owner',))
        msg = await ctx.send('Please wait...')
        start_time = datetime.now()
        m = {'messages': 0}
        async def msg_task(m):
            while True:
                await self.bot.wait_for('message')
                m['messages'] += 1
        task = self.loop.create_task(msg_task(m))
        await asyncio.sleep(8)
        task.cancel()
        time_elapsed = datetime.now() - start_time
        time_elapsed = time_elapsed.total_seconds()
        await msg.edit(content='I seem to be getting ' + str(round(m['messages'] / time_elapsed, 2)) + ' messages per second.')

    @commands.command(aliases=['edata'])
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
            await ctx.send(':warning: **Invalid JSON data!**')
        else:
            sembed = SemiEmbed(embed_obj)
            try:
                await ctx.send(embed=sembed)
            except discord.HTTPException as e:
                if '400' in str(e):
                    await ctx.send(':warning: **Couldn\'t send embed, check your data!**')
                else:
                    raise e

def setup(bot):
    c = Owner(bot)
    bot.add_cog(c)
