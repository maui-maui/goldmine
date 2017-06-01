"""Where all the good stuff happens in the bot."""
import asyncio
import random
import inspect
import subprocess
import os
import sys
import traceback
import re
import shutil
import math
import logging
import async_timeout
import discord
import aiohttp
import util.json as json
from discord.ext import commands
from contextlib import suppress
from fnmatch import filter
from datetime import datetime
from discord.ext.commands.bot import StringView, CommandError, CommandNotFound
from convert_to_old_syntax import cur_dir, rc_files
from properties import storage_backend
from .datastore import DataStore
from .const import *
from .fake import FakeObject
from .token import is_bot
from .ext_context import ExtContext
import distutils.dir_util
import util.token as token

try:
    from ex_props import store_path
    opath = store_path
except ImportError:
    opath = None

try:
    import psutil
    have_psutil = True
except ImportError:
    have_psutil = False
    if sys.platform in ['linux', 'linux2', 'darwin']:
        import resource

class GoldBot(commands.AutoShardedBot):
    """The brain of the bot, GoldBot."""

    def __init__(self, **options):
        self.logger = logging.getLogger('bot')
        self.loop = asyncio.get_event_loop()
        self.cog_http = aiohttp.ClientSession(loop=self.loop)
        self.perm_mask = '1609825363' # 66321741 = full
        self.start_time = datetime.now()
        self.dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].core_file))

        self.storepath = os.path.join(self.dir, 'storage.')
        if storage_backend not in DataStore.exts:
            self.logger.critical('Invalid storage backend specified, quitting!')

        self.store = None
        if opath:
            self.store = DataStore(storage_backend, path=opath, join_path=False)
        else:
            self.store = DataStore(storage_backend)

        self.lib_version = '.'.join(map(str, discord.version_info))
        self.store_writer = self.loop.create_task(self.store.commit_task())
        self.have_resource = sys.platform in ['linux', 'linux2', 'darwin']

        self.loop.create_task(self.update_emote_data())
        self.emotes = {}

        path_templates = {
            'dl': ('cogs',),
            'ex': ('cogs.txt',),
            'dis': ('disabled_cogs.txt',),
            'init_dl': ('cogs', '__init__.py'),
            'data': ('data',),
            'cog_json': ('data', 'cogs.json'),
            'cog_py': ('cogs', 'cog.py')
        }
        paths = {}
        for path in path_templates:
            paths[path] = os.path.join(self.dir, *path_templates[path])

        for name in ['dl', 'data']: # Dirs
            p = paths[name]
            with suppress(OSError):
                if not os.path.exists(p):
                    os.makedirs(p)
        for name in ['ex', 'dis']: # Files
            p = paths[name]
            with suppress(OSError):
                if not os.path.exists(p):
                    f = open(p, 'a')
                    f.close()
        with suppress(OSError):
            if not os.path.exists(paths['init_dl']):
                with open(paths['init_dl'], 'w+') as f:
                    f.write('"""Placeholder to make Python recognize this as a module."""\n')
        with suppress(IOError):
            if not os.path.exists(paths['cog_py']):
                shutil.copy2(os.path.join(self.dir, 'default_cogs', 'cog.py'), paths['cog_py'])

        self.disabled_cogs = []
        with open(paths['dis'], 'r') as f:
            self.disabled_cogs = [c.rstrip() for c in f.readlines()]

        self.enabled_cogs = []
        with open(paths['ex'], 'r') as f:
            self.enabled_cogs = [c.rstrip() for c in f.readlines()]

        if not os.path.exists(paths['cog_json']):
            with open(paths['cog_json'], 'a') as f:
                f.write('{}')

        if 'nobroadcast' not in self.store.store:
            self.store.store['nobroadcast'] = [110373943822540800]
        if 'owner_messages' not in self.store.store:
            self.store.store['owner_messages'] = []

        self.command_calls = {}
        self.app_info = None
        self.owner_user = None
        self.is_restart = False
        self.selfbot = not is_bot

        if 'utils_revision' not in self.store.store:
            self.store['utils_revision'] = 1
        if self.store.store['utils_revision'] < 2:
            distutils.dir_util.copy_tree(os.path.join(cur_dir, 'default_cogs', 'utils'), os.path.join(cur_dir, 'cogs', 'utils') + os.path.sep)
            self.store['utils_revision'] = 2

        self.start_reported = False
        super().__init__(**options)
        self.all_commands = {}

    async def on_ready(self):
        """On_ready event for when the bot logs into Discord."""
        self.logger.info('Bot has logged into Discord, ID ' + str(self.user.id))
        if self.user.bot:
            self.app_info = await self.application_info()
            self.owner_user = self.app_info.owner
        else:
            self.owner_user = self.user
        self.logger.info('Owner information filled.')
        if not self.selfbot and len(self.guilds) >= 75:
            key = ('Ready event emitted.' if self.start_reported else "I've just started up!")
            await self.send_message(self.owner_user, key + "\nThe time is **%s**." % datetime.now().strftime(absfmt))
            if not self.start_reported:
                self.start_reported = True

    async def on_message(self, msg):
        try:
            myself = msg.guild.me
        except AttributeError:
            myself = self.user
        if self.selfbot:
            try:
                cmdfix = self.store['properties']['global']['selfbot_prefix']
            except KeyError:
                cmdfix = myself.name[0].lower() + '.'
            prefix_convo = False
            do_logic = msg.author.id == self.user.id
        else:
            cmdfix = self.store.get_cmdfix(msg)
            prefix_convo = (self.store.get_prop(msg, 'prefix_answer')) in bool_true
            do_logic = msg.author.id != self.user.id
        prefix_help = (msg.guild.id if msg.guild else None) != 110373943822540800 # DBots
        lname = myself.display_name.lower()
        if do_logic:
            if msg.author.bot:
                if not self.selfbot:
                    self.dispatch('bot_message', msg)
            else:
                if self.selfbot:
                    if msg.content.startswith(cmdfix):
                        await self.process_commands(msg, cmdfix)
                    else:
                        self.dispatch('not_command', msg)
                    return
                if isinstance(msg.channel, discord.abc.GuildChannel):
                    if not msg.content.startswith(cmdfix):
                        self.dispatch('not_command', msg)
                if isinstance(msg.channel, discord.abc.PrivateChannel):
                    if msg.content.startswith(cmdfix):
                        await self.process_commands(msg, cmdfix)
                    else:
                        self.dispatch('pm', msg)
                elif msg.content.lower().startswith(lname + ' ') and prefix_convo:
                    self.dispatch('prefix_convo', msg, lname)
                elif (msg.content.lower() in ['prefix', 'prefix?']) and prefix_help:
                    await msg.channel.send('**Current guild command prefix is: **`' + cmdfix + '`')
                else:
                    if msg.content.startswith(cmdfix):
                        await self.process_commands(msg, cmdfix)
                    elif myself.mentioned_in(msg) and ('@everyone' not in msg.content) and ('@here' not in msg.content):
                        self.dispatch('mention', msg)

    async def on_error(self, *a, **b):
        await self.cogs['Errors'].on_error(*a, **b)

    async def on_guild_join(self, guild):
        """Send the bot introduction message when invited."""
        self.logger.info('New guild: ' + guild.name)
        if self.selfbot: return
        try:
            await self.send_message(guild.default_channel, join_msg)
        except discord.Forbidden:
            satisfied = False
            c_count = 0
            try_channels = list(guild.channels)
            channel_count = len(try_channels) - 1
            while not satisfied:
                with suppress(discord.Forbidden, discord.HTTPException):
                    await self.send_message(try_channels[c_count], join_msg)
                    satisfied = True
                if c_count > channel_count:
                    self.logger.warning('Couldn\'t announce join to guild ' + guild.name)
                    satisfied = True
                c_count += 1

    async def on_guild_remove(self, guild):
        """Update the stats."""
        self.logger.info('Lost a guild: ' + guild.name)

    async def process_commands(self, message, prefix):
        """This function processes the commands that have been registered."""
        await self.invoke(self.get_context(message, prefix))

    def get_context(self, message, prefix):
        view = StringView(message.content)
        view.skip_string(prefix)
        ctx = ExtContext(prefix=prefix, view=view, bot=self, message=message)

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def invoke(self, ctx):
        if ctx.command is not None:
            try:
                await ctx.command.invoke(ctx)
                if ctx.command.name in self.command_calls:
                    self.command_calls[ctx.command.name] += 1
                else:
                    self.command_calls[ctx.command.name] = 1
            except CommandError as e:
                await ctx.command.dispatch_error(ctx, e)
        elif ctx.invoked_with:
            exc = CommandNotFound('Command "{}" is not found'.format(ctx.command))
            self.dispatch('command_error', ctx, exc)

    def format_uptime(self):
        """Return a human readable uptime."""
        s = lambda n: '' if n == 1 else 's'
        fmt = '{0} day{4} {1} hour{5} {2} minute{6} {3} second{7}'
        time_diff = datetime.now() - self.start_time
        time_mins = divmod(time_diff.total_seconds(), 60)
        time_hrs = divmod(time_mins[0], 60)
        time_days = divmod(time_hrs[0], 24)
        final = fmt.format(int(time_days[0]), int(time_days[1]), int(time_hrs[1]), int(time_mins[1]),
                           s(time_days[0]), s(time_days[1]), s(time_hrs[1]), s(time_mins[1]))
        return final

    async def send_cmd_help(self, ctx):
        """Send command help for a command or subcommand."""
        if ctx.invoked_subcommand:
            pages = self.formatter.format_help_for(ctx, ctx.invoked_subcommand)
            for page in pages:
                await ctx.send(page)
        else:
            pages = self.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await ctx.send(page)

    def get_ram(self):
        """Get the bot's RAM usage info."""
        if have_psutil: # yay!
            mu = psutil.Process(os.getpid()).memory_info().rss
            return (True, mu / 1000000, mu / 1048576)
        else: # aww
            raw_musage = 0
            got_conversion = False
            musage_dec = 0
            musage_hex = 0
            if sys.platform.startswith('linux'): # Linux & Windows report in kilobytes
                raw_musage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                got_conversion = True
                musage_dec = raw_musage / 1000
                musage_hex = raw_musage / 1024
            elif sys.platform == 'darwin': # Mac reports in bytes
                raw_musage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                got_conversion = True
                musage_dec = raw_musage / 1000000 # 1 million. 1000 * 1000
                musage_hex = raw_musage / 1048576 # 1024 * 1024
            if got_conversion:
                return (got_conversion, musage_dec, musage_hex)
            else:
                return (got_conversion,)

    async def update_emote_data(self):
        """Fetch Twitch and FrakerFaceZ emote mappings."""
        with open(os.path.join(cur_dir, 'assets', 'emotes_twitch_global.json')) as f:
            twitch_global = json.loads(f.read())['emotes']
        with open(os.path.join(cur_dir, 'assets', 'emotes_twitch_subscriber.json')) as f:
            twitch_sub = json.loads(f.read())
        twitch_subscriber = {e: {'description': '\u200b', 'image_id': twitch_sub[e], 'first_seen': None} for e in twitch_sub}
        self.emotes['twitch'] = {**twitch_global, **twitch_subscriber}
        with open(os.path.join(cur_dir, 'assets', 'emotes_ffz.json')) as f:
            self.emotes['ffz'] = json.loads(f.read())
        with open(os.path.join(cur_dir, 'assets', 'emotes_bttv.json')) as f:
            raw_json = json.loads(f.read())
            bttv_v1 = {n: 'https:' + raw_json[n] for n in raw_json}
        with open(os.path.join(cur_dir, 'assets', 'emotes_bttv_2.json')) as f:
            raw_json2 = json.loads(f.read())
            bttv_v2 = {n: 'https://cdn.betterttv.net/emote/' + str(raw_json2[n]) + '/1x' for n in raw_json2}
        self.emotes['bttv'] = {**bttv_v1, **bttv_v2}

    def del_command(self, *names):
        """Remove a command and its aliases."""
        for name in names:
            for a in self.all_commands[name].aliases:
                del self.all_commands[a]
            del self.all_commands[name]
