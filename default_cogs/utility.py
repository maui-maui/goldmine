"""Definition of the bot's Utility module."""
import asyncio
import random
import re
import sys
import time
import aiohttp
import async_timeout
import discord
import os
import socket
import contextlib
import textwrap
import util.commands as commands
import util.json as json
from contextlib import suppress
from collections import OrderedDict
from datetime import datetime, timedelta
from fnmatch import filter
from io import BytesIO, StringIO
from util.const import _mention_pattern, _mentions_transforms, home_broadcast, absfmt, status_map, ch_fmt, eval_blocked, v_level_map
from util.fake import FakeContextMember, FakeMessageMember
from util.func import bdel, encode as b_encode, decode as b_decode, smartjoin
from util.asizeof import asizeof
from util.perms import check_perms, or_check_perms
import util.dynaimport as di
from .cog import Cog

for mod in ['unicodedata', 'elizabeth',
            'qrcode', 'warnings', 'tesserocr', 'base64']:
    globals()[mod] = di.load(mod)
mclib = di.load('util.mclib')
xkcd = di.load('util.xkcd')

have_pil = True
try:
    from PIL import Image, ImageOps
except ImportError:
    have_pil = False

class Utility(Cog):
    """Random commands that can be useful here and there.
    Settings, properties, and other stuff can be found here.
    """
    def __init__(self, bot):
        self.stopwatches = {}
        super().__init__(bot)
        self.logger = self.logger.getChild('utility')

    @commands.command(pass_context=True, no_pm=True)
    async def icon(self, ctx):
        """Retrive the current server's icon.
        Usage: icon"""
        sname = '**' + ctx.message.server.name + '**'
        iurl = ctx.message.server.icon_url
        if iurl:
            await self.bot.say('Here is the link to the icon for ' + sname + ': <' + iurl + '>')
        else:
            await self.bot.say('The current server, ' + sname + ', does not have an icon set! :slight_frown:')

    @commands.command(pass_context=True, aliases=['echo'])
    async def say(self, ctx, *, stuffs: str):
        """Repeat your message.
        Usage: say [message]"""
        if not self.bot.selfbot:
            try:
                await self.bot.delete_message(ctx.message)
            except discord.Forbidden:
                pass
        await self.bot.say(stuffs.replace('@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')[:2000])

    @commands.command(pass_context=True, aliases=['whois', 'who', 'userinfo', 'uinfo', 'u'])
    async def user(self, ctx, *users: str):
        """Get tons of info on an user or some users.
        Spaces, multiuser, and cross-server IDs work.
        Usage: user {user(s)}"""
        targets = []
        s = ctx.message.server
        if users: # huge complicated mess for spaces,
                  # multiuser, nicknames, mentions, IDs,
                  # names, and more in one go.
            members = {}
            for i in getattr(s, 'members', []):
                members[i.mention] = i
                members[i.id] = i
                members[i.display_name] = i
                members[i.name] = i
                members[str(i)] = i
            for i in users:
                try:
                    member = s.get_member(i)
                except AttributeError:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                if member:
                    targets.append(member)
                else:
                    try:
                        member = await self.bot.get_user_info(i)
                    except discord.HTTPException:
                        member = None
                    if member:
                        targets.append(member)
            names = []
            _i = 0
            while _i < len(users):
                names.append(users[_i])
                with suppress(KeyError):
                    if ' '.join(names) in members:
                        targets.append(members[' '.join(names)])
                        names = []
                    elif _i + 1 == len(users):
                        targets.append(members[users[0]])
                        _i = -1
                        users = users[1:]
                        names = []
                _i += 1
            if not targets:
                await self.bot.say('**No matching users, try again! Name, nickname, name#0000 (discriminator), or ID work. Spaces do, too!**')
                return
        else:
            targets.append(ctx.message.author)
        targets = list(OrderedDict.fromkeys(targets))
        for target in targets:
            au = target.avatar_url
            avatar_link = (au if au else target.default_avatar_url)
            d_name = target.display_name
            try:
                t_roles = target.roles
            except AttributeError:
                t_roles = []
            try:
                t_game = target.game
            except AttributeError:
                t_game = None
            b_roles = []
            c_srv = False
            c_sown = False
            try:
                tg_ctx = FakeContextMember(FakeMessageMember(target), self.bot)
            except AttributeError:
                tg_ctx = None
            else:
                c_srv = check_perms(tg_ctx, ('manage_server',))
                c_sown = check_perms(tg_ctx, ('server_owner',))
            c_own = target.id == self.bot.owner_user.id
            c_adm = target.id in self.bot.store['bot_admins']
            is_server = isinstance(target, discord.Member)
            if c_own:
                b_roles.append('Bot Owner')
            if c_adm:
                b_roles.append('Bot Admin')
            if c_srv:
                b_roles.append('Server Admin')
            with suppress(ValueError, AttributeError):
                t_roles.remove(target.server.default_role)
            r_embed = discord.Embed(color=random.randint(0, 256**3-1))
            r_embed.set_author(name=str(target), icon_url=avatar_link, url=avatar_link)
            r_embed.set_thumbnail(url=avatar_link) #top right
            r_embed.set_footer(text=str(target), icon_url=avatar_link)
            r_embed.add_field(name='Nickname', value=('No nickname set 😦' if d_name == target.name else d_name))
            r_embed.add_field(name='User ID', value=target.id)
            r_embed.add_field(name='Creation Time', value=target.created_at.strftime(absfmt))
            r_embed.add_field(name='Server Join Time', value=target.joined_at.strftime(absfmt) if is_server else 'Couldn\'t fetch')
            r_embed.add_field(name='Server Roles', value=', '.join([str(i) for i in t_roles]) if t_roles else 'User has no server roles 😦')
            r_embed.add_field(name='Bot Roles', value=', '.join(b_roles) if b_roles else 'User has no bot roles 😦')
            r_embed.add_field(name='Status', value=status_map[str(target.status)] if is_server else 'Couldn\'t fetch')
            try:
                r_embed.add_field(name='Currently Playing', value=(str(t_game) if t_game else 'Nothing 😦'))
            except TypeError:
                r_embed.add_field(name='Currently Playing', value='Nothing 😦')
            await self.bot.say(embed=r_embed)

    @commands.command(pass_context=True, aliases=['server', 's', 'sinfo', 'infos', 'guildinfo', 'guild', 'ginfo', 'infog'], no_pm=True)
    async def serverinfo(self, ctx):
        """Get loads of info about this server.
        Usage: serverinfo"""
        target = self.bot.user
        s = ctx.message.server
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        ach = s.channels
        chlist = [len(ach), 0, 0]
        for i in ach:
            if i.type == discord.ChannelType.text:
                chlist[1] += 1
            else:
                chlist[2] += 1
        iurl = s.icon_url
        s_reg = str(s.region)
        r_embed = discord.Embed(color=random.randint(0, 256**3-1))
        if iurl:
            thing = {'url': iurl}
        else:
            thing = {}
        r_embed.set_author(name=s.name, **thing, icon_url=(iurl if iurl else avatar_link))
        r_embed.set_footer(text=str(target), icon_url=avatar_link)
        if iurl:
            r_embed.set_image(url=iurl)
        r_embed.add_field(name='ID', value=s.id)
        r_embed.add_field(name='Members', value=len(s.members))
        r_embed.add_field(name='Channels', value=ch_fmt.format(*[str(i) for i in chlist]))
        r_embed.add_field(name='Roles', value=len(s.roles))
        r_embed.add_field(name='Custom Emojis', value=len(s.emojis))
        r_embed.add_field(name='Region (Location)', value=str(s.region).replace('-', ' ').title().replace('Eu ', 'EU ').replace('Us ', 'US ').replace('Vip', 'VIP '))
        r_embed.add_field(name='Owner', value=str(s.owner))
        r_embed.add_field(name='Default Channel', value=f'<#{s.default_channel.id}>\n(#{s.default_channel.name})')
        r_embed.add_field(name='Admins Need 2FA', value=('Yes' if s.mfa_level else 'No'))
        r_embed.add_field(name='Verification Level', value=v_level_map[str(s.verification_level)])
        await self.bot.say(embed=r_embed)

    @commands.command(pass_context=True, aliases=['gm', 'goldmine', 'aboutme', 'me', 'about'])
    async def info(self, ctx):
        """Get bot info.
        Usage: info"""
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        ach = self.bot.get_all_channels()
        chlist = [0, 0, 0]
        for i in ach:
            chlist[0] += 1
            if i.type == discord.ChannelType.text:
                chlist[1] += 1
            else:
                chlist[2] += 1
        up = await self.bot.format_uptime()
        ram = await self.bot.get_ram()
        got_conversion = ram[0]
        emb = discord.Embed(color=random.randint(0, 256**3-1))
        emb.set_author(name=str(target), url='https://khronodragon.com/', icon_url=avatar_link)
        emb.set_footer(text='Made in Python 3.6+ with Discord.py %s' % self.bot.lib_version, icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/400px-Python-logo-notext.svg.png')
        emb.add_field(name='Servers', value=len(self.bot.servers))
        emb.add_field(name='Author', value='Dragon5232#1841')
        emb.add_field(name='Uptime', value=up)
        emb.add_field(name='Local Time', value=time.strftime(absfmt, time.localtime()))
        emb.add_field(name='Git Revision', value=self.bot.git_rev)
        emb.add_field(name='Cogs Loaded', value=len(self.bot.cogs))
        emb.add_field(name='Command Calls', value=sum(self.bot.command_calls.values()))
        emb.add_field(name='Memory Used', value=(str(round(ram[1], 1)) + ' MB (%s MiB)' % str(round(ram[2], 1))) if got_conversion else 'Couldn\'t fetch')
        emb.add_field(name='Modules Loaded', value=len(self.bot.modules))
        emb.add_field(name='Members Seen', value=len(list(self.bot.get_all_members())))
        emb.add_field(name='Channels', value=ch_fmt.format(*[str(i) for i in chlist]))
        emb.add_field(name='Custom Emojis', value=len(list(self.bot.get_all_emojis())))
        emb.add_field(name='Commands', value=str(len(self.bot.commands)))
        emb.add_field(name='ID', value=target.id)
        if self.bot.user.id == '239775420470394897':
            emb.add_field(name='Invite Link', value='https://tiny.cc/goldbot')
        await self.bot.say(home_broadcast, embed=emb)

    @commands.cooldown(1, 2.95, type=commands.BucketType.server)
    @commands.command(pass_context=True, aliases=['pong', 'delay', 'net', 'network', 'lag', 'netlag', 'latency'])
    async def ping(self, ctx):
        """Ping, pong!
        Usage: ping"""
        begin_time = datetime.now()
        msg = await self.bot.send_message(ctx.message.channel, '**Pong!** | I wonder how long this takes...')
        await self.bot.edit_message(msg, '**Pong!** | I really do wonder...')
        time_diff = datetime.now() - begin_time
        await self.bot.edit_message(msg, '**Pong!** Responded in %sms.' % str(round((time_diff.total_seconds() / 2) * 1000, 2)))

    @commands.command(pass_context=True, aliases=['ram', 'memory', 'usage', 'mem', 'musage'])
    async def uptime(self, ctx):
        """Report the current uptime of the bot.
        Usage: uptime"""
        up = await self.bot.format_uptime()
        ram = await self.bot.get_ram()
        got_conversion = ram[0]
        ram_final = (' RAM usage is **' + str(round(ram[1], 1)) + ' MB (%s MiB)**.' % str(round(ram[2], 1))) if got_conversion else ''
        await self.bot.say(ctx.message.author.mention + ' I\'ve been up for **' + up + '**.' + ram_final)

    @commands.command(pass_context=True, aliases=['link', 'invlink', 'addbot', 'botadd'])
    async def invite(self, ctx, *rids: str):
        """Generate an invite link for myself or another bot.
        Usage: invite {optional: bot ids}"""
        ids = list(rids)
        msg = []
        if not ids:
            ids.append(self.bot.user.id)
        for iid in ids:
            try:
                int(iid)
                if len(iid) in range(16, 20):
                    if iid == self.bot.user.id:
                        msg.append('https://discordapp.com/api/oauth2/authorize?client_id={}&scope=bot&permissions={}'.format(iid, self.bot.perm_mask))
                    else:
                        msg.append('https://discordapp.com/api/oauth2/authorize?client_id=%s&scope=bot&permissions=3072' % iid)
                else:
                    msg.append('**Invalid ID **`%s`** (must be 18 numbers)!**' % iid)
            except ValueError:
                msg.append('**Invalid ID **`%s`** (must be made of numbers)!**' % iid)
        if msg:
            await self.bot.say('\n'.join(msg))

    @commands.command(aliases=['homeland', 'web', 'website', 'webpage'])
    async def home(self):
        """Get the link to my homeland.
        Usage: home"""
        await self.bot.say(home_broadcast)

    async def poll_task(self, emojis, msg, poll_table):
        while True:
            fnr = await self.bot.wait_for_reaction(emoji=emojis, message=msg, check=lambda r, a: not a == msg.server.me)
            r = fnr.reaction
            if fnr.user not in poll_table[str(r.emoji)]:
                poll_table[str(r.emoji)].append(fnr.user)

    @commands.cooldown(1, 5, type=commands.BucketType.user)
    @commands.command(pass_context=True)
    async def poll(self, ctx, *rquestion: str):
        """Start a public poll with reactions.
        Usage: poll [emojis] [question] [time in seconds]"""
        async def cem_help(emojis, raw_c_emojis, cem_map, c_emojis):
            """Custom emoji helper."""
            if raw_c_emojis:
                try:
                    for i in ctx.message.server.emojis:
                        cem_map[str(i)] = i
                except AttributeError:
                    return
                for i in raw_c_emojis:
                    try:
                        c_emojis.append(cem_map[i])
                    except KeyError:
                        await self.bot.say('**Custom emoji `%s` doesn\'t exist!**' % i)
                        return
                emojis += c_emojis
        question = ''
        if rquestion:
            question = ' '.join(rquestion)
        else:
            await self.bot.say('**You must specify a question!**')
            return
        stime = 0.0
        cem_map = {}
        highpoints = None
        try:
            stime = float(rquestion[-1:][0])
        except ValueError:
            await self.bot.say('**You must provide a valid poll time!**')
            return
        _question = question.split()
        del _question[-1:]
        question = ' '.join(_question)
        try: # UCS-4
            highpoints = re.compile(u'[\U00010000-\U0010ffff\u2615]')
        except re.error: # UCS-2
            highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
        u_emojis = re.findall(highpoints, question)
        raw_c_emojis = re.findall(re.compile(r'<:[a-z]+:[0-9]{18}>', flags=re.IGNORECASE), question)
        c_emojis = []
        emojis = u_emojis
        await cem_help(emojis, raw_c_emojis, cem_map, c_emojis)
        emojis = list(OrderedDict.fromkeys(emojis))
        for ri in emojis:
            i = str(ri)
            question = question.replace(' ' + i, '')
            question = question.replace(i + ' ', '')
            question = question.replace(i, '')
        question = question.strip()
        if not emojis:
            await self.bot.say('**You must specify some emojis!**')
            return
        elif len(emojis) < 2:
            await self.bot.say('**You need at least 2 emojis to poll!**')
            return
        msg_key = ctx.message.author.mention + ' is now polling:\n    \u2022 ' + question + '\n'
        msg = await self.bot.say(msg_key + '**POLL NOT ACTIVE YET, ADDING REACTIONS.**')
        for emoji in emojis:
            await self.bot.add_reaction(msg, emoji)
            await asyncio.sleep(0.14)
        await self.bot.edit_message(msg, msg_key + '**POLL IS NOW ACTIVE. Give it a vote!**')
        emojis = list(emojis)
        poll_table = OrderedDict((str(i), []) for i in emojis)
        task = self.loop.create_task(self.poll_task(emojis, msg, poll_table))
        await asyncio.sleep(stime)
        task.cancel()
        _vote_table = {i: len(poll_table[i]) for i in poll_table}
        vote_table = OrderedDict(reversed(sorted(_vote_table.items(), key=lambda t: t[1])))
        _totals = '\n'.join([str(i) + ': {0} votes'.format(str(vote_table[i])) for i in vote_table])
        winner = max(vote_table, key=vote_table.get)
        await self.bot.say('**Poll time is over, stopped! Winner is...** ' + str(winner) + '\nResults were:\n' + _totals)
        await self.bot.edit_message(msg, msg_key + '**POLL HAS ALREADY FINISHED.**')
        #await self.bot.say('VT `' + str(vote_table) + '`')

    @commands.command(aliases=['sw'], pass_context=True)
    async def stopwatch(self, ctx):
        """A stopwatch for your convenience."""
        author = ctx.message.author
        if not author.id in self.stopwatches:
            self.stopwatches[author.id] = int(time.perf_counter())
            await self.bot.say(author.mention + ' Stopwatch started!')
        else:
            tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
            tmp = str(timedelta(seconds=tmp))
            await self.bot.say(author.mention + ' Stopwatch stopped! Time: **' + tmp + '**')
            self.stopwatches.pop(author.id, None)

    @commands.command(pass_context=True, name='id', aliases=['myid', 'sid', 'serverid'])
    async def _id(self, ctx):
        """Get all the current scope IDs."""
        fmt = '''**ID Party!**
Server ID: `{0.server.id}` (same as default channel ID and @\u200beveryone role ID!)
Channel ID: `{0.channel.id}`
Your ID: `{0.author.id}`
Server Owner\'s ID: `{0.server.owner.id}`
**You can also look up the ID of other people with** `{1.prefix}user [name / id / mention]`**.**'''
        if not ctx.message.server:
            class C:
                id = 'Not applicable'
            ctx.message.server = C
        await self.bot.say(fmt.format(ctx.message, ctx))

    @commands.command(pass_context=True, aliases=['memegen'], hidden=True)
    async def meme(self, ctx, *, pre_text: str):
        """Generate a meme!
        Usage: meme [top text] [bottom text]"""
        char_table = {
            '-': '--',
            '_': '__',
            '?': '~q',
            '%': '~p',
            '#': '~h', # TODO: make
            '/': '~s',
            '"': "''",
            '\n': ' '
        }
        for key in char_table:
            pre_text = pre_text.replace(key, char_table[key])
        pre_text = pre_text.replace('    ', '__bottom__')
        pre_text = pre_text.replace(' ', '-')
        if '__bottom__' in pre_text:
            segments = pre_text.split('__bottom__')
        else:
            segments = textwrap.wrap(pre_text, width=int(len(pre_text) / 2))
        async with aiohttp.ClientSession(loop=asyncio.get_event_loop()) as session:
            with async_timeout.timeout(10):
                async with session.get('https://memegen.link/api/templates/') as r:
                    rtext = await r.text()
                    templates = list(json.loads(rtext).values())
                rtemp = random.choice(templates)
                meme_url = rtemp + '/' + segments[0] + '/' + segments[1] + '.jpg'
                async with session.get(meme_url) as r:
                    raw_image = await r.read()
        await self.bot.send_file(ctx.message.channel, fp=BytesIO(raw_image), filename='meme.jpg')

    @commands.command(pass_context=True, aliases=['statistics', 'servers', 'channels', 'members', 'users', 'seen'])
    async def stats(self, ctx):
        """Dump some of my stats. Full version = info command.
        Usage: stats"""
        fmt = '''{0.author.mention} Here are my stats: (get even more with `{1}info`!)
**Servers**: {2}
**Channels**: {3}
**Members**: {4}
**Uptime**: {5}'''
        up = await self.bot.format_uptime()
        await self.bot.say(fmt.format(ctx.message, ctx.prefix,
                           len(self.bot.servers),
                           sum(len(s.channels) for s in self.bot.servers),
                           sum(len(s.members) for s in self.bot.servers),
                           up))

    @commands.command(aliases=['randcolor', 'randc', 'rc', 'randomcolor', 'colorgen', 'gcolor', 'gencolor', 'randcolour', 'randomcolour', 'colourgen', 'gcolour', 'gencolour'])
    async def rcolor(self):
        """Generate a random color.
        Usage: rcolor"""
        col_rgb = [random.randint(1, 255) for i in range(0, 3)]
        col_str = '0x%02X%02X%02X' % (col_rgb[0], col_rgb[1], col_rgb[2])
        await self.bot.say(embed=discord.Embed(color=int(col_str, 16), title='Hex: ' + col_str.replace('0x', '#') + ' | RGB: ' + ', '.join([str(c) for c in col_rgb]) + ' | Integer: ' + str(int(col_str, 16))))

    @commands.command(aliases=['character', 'char', 'cinfo', 'unicode'])
    async def charinfo(self, *, uchars: str):
        """Get the Unicode info for a character or characters.
        Usage: charinfo [character(s)]"""
        no_preview = [
            '\u0020',
            '\uFEFF'
        ]
        cinfo = commands.Paginator(prefix='', suffix='', max_size=(1999 if self.bot.selfbot else 2000))
        for char in list(uchars.replace('\n', '')):
            hexp = str(hex(ord(char))).replace('0x', '').upper()
            while len(hexp) < 4:
                hexp = '0' + hexp
            preview = f' (`{char}`)'
            cinfo.add_line(f'U+{hexp} {unicodedata.name(char)} {char}' + (preview if char not in no_preview else ''))
        if len(cinfo.pages) > 5:
            await self.bot.say('Too long, trimming to 5 pages.')
        for page in cinfo.pages[0:5]:
            await self.bot.say(page)

    @commands.command()
    async def encode(self, *, content: str):
        """Encode your text into Goldmine's encoding!
        Usage: encode [text]"""
        await self.bot.say('```' + (b_encode(content)) + '```')
    @commands.command()
    async def decode(self, *, content: str):
        """Decode your text from Goldmine's encoding!
        Usage: decode [encoded text]"""
        await self.bot.say('```' + (b_decode(content)) + '```')

    @commands.cooldown(1, 6.75, type=commands.BucketType.user)
    @commands.command(pass_context=True, aliases=['mc'])
    async def minecraft(self, ctx, *, server_ip: str):
        """Get information about a Minecraft server.
        Usage: minecraft [server address]"""
        port = 25565
        port_split = server_ip.split(':')
        server = port_split[0].replace('/', '')
        if len(port_split) > 1:
            try:
                port = int(port_split[1])
            except ValueError:
                pass
        if ('.' not in server) or (' ' in server_ip):
            await self.bot.say(':warning: Invalid address.')
            return
        try:
            self.logger.info('Connecting to Minecraft server ' + server + ':' + str(port) + '...')
            with async_timeout.timeout(5):
                data = await self.loop.run_in_executor(None, mclib.get_info, server, port)
        except Exception as e:
            await self.bot.send_message(ctx.message.channel, f':warning: Couldn\'t get server info for `{server}:{port}`.')
            return
        desc = ''
        server_type = 'Vanilla'
        def decode_extra_desc():
            final = []
            format_keys = {
                'bold': '**',
                'italic': '*',
                'underlined': '__',
                'strikethrough': '~~'
            }
            for e in data['description']['extra']:
                item = e['text']
                for fkey in format_keys:
                    if e.get(fkey, False):
                        int_key = '%{f:' + fkey + '}$'
                        item = int_key + item + int_key
                final.append(item)
            final = ''.join(final)
            for fkey in format_keys:
                int_key = '%{f:' + fkey + '}$'
                final = final.replace(int_key * 3, '').replace(int_key * 2, '')
                final = final.replace(int_key, format_keys[fkey])
            return final
        if isinstance(data['description'], dict):
            if 'text' in data['description']:
                if data['description']['text']:
                    desc = data['description']['text']
                else:
                    desc = decode_extra_desc()
            else:
                desc = decode_extra_desc()
        elif isinstance(data['description'], str):
            desc = data['description']
        else:
            desc = str(data['description'])
        def decode_section_code():
            formats = {
                'l': '**',
                'n': '__',
                'o': '*',
                'k': '',
                'm': '~~',
                'k': '**',
                'r': ''
            } # k = obf, r = reset
            state = ''
        desc = re.sub(r'\u00a7[4c6e2ab319d5f780lnokmr]', '', desc)
        rc = random.randint(0, 256**3-1)
        emb = discord.Embed(title=server + ':' + str(port), description=desc, color=rc)
        try:
            target = ctx.message.server.me
        except AttributeError:
            target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        emb.set_footer(text=target.name, icon_url=avatar_link)
        emb.add_field(name='Players', value=str(data['players']['online']) + '/' + str(data['players']['max']))
        if data['players'].get('sample', False):
            content = re.sub(r'\u00a7[4c6e2ab319d5f78lnokmr]', '', smartjoin([p['name'] for p in data['players']['sample']]))
            if len(content) <= 1024:
                emb.add_field(name='Players Online', value=content)
            else:
                pages = textwrap.wrap(content, width=1024)
                for page in pages:
                    emb.add_field(name='Players Online', value=page)
        emb.add_field(name='Version', value=re.sub(r'\u00a7[4c6e2ab319d5f78lnokmr]', '', data['version']['name']))
        emb.add_field(name='Protocol Version', value=data['version']['protocol'])
        if 'modinfo' in data:
            if 'modList' in data['modinfo']:
                if data['modinfo']['modList']:
                    content = smartjoin([m['modid'].title() + ' ' +
                              m['version'] for m in data['modinfo']['modList']])
                    if len(content) <= 1024:
                        emb.add_field(name='Mods', value=content)
                    else:
                        pages = textwrap.wrap(content, width=1024)
                        for page in pages:
                            emb.add_field(name='Mods', value=page)
                else:
                    emb.add_field(name='Use of Mods', value='This server appears to fake its identity, so Forge clients will send their mod list.')
            if data['modinfo'].get('type', False):
                t = data['modinfo']['type']
                if t.lower() == 'fml':
                    server_type = 'Forge / FML'
                else:
                    server_type = t.title()
        emb.add_field(name='Server Type', value=server_type)
        emb.add_field(name='Ping', value=str(round(data['latency_ms'], 2)) + 'ms')
        await self.bot.say(embed=emb)

    @commands.cooldown(1, 20, type=commands.BucketType.user)
    @commands.command(pass_context=True)
    async def contact(self, ctx, *, message: str):
        """Contact the bot owner with a message.
        Usage: contact [message]"""
        for m in ctx.message.mentions:
            message = message.replace(m.mention, '@' + str(m))
        msg_object = {
            'message': message,
            'user': str(ctx.message.author),
            'nick': ctx.message.author.display_name,
            'message_id': ctx.message.id,
            'user_id': ctx.message.author.id,
            'channel_id': ctx.message.channel.id,
            'pm': ctx.message.channel.is_private,
            'time': str(ctx.message.timestamp),
            'timestamp': ctx.message.timestamp.timestamp(),
            'contains_mention': bool(ctx.message.mentions),
        }
        if ctx.message.server:
            msg_object.update({
                'server': ctx.message.server.name,
                'server_id': ctx.message.server.id,
                'server_members': len(ctx.message.server.members),
                'channel': ctx.message.channel.name
            })
        self.bot.store['owner_messages'].append(msg_object)
        await self.bot.say(':thumbsup: Message recorded.')

    @commands.command(pass_context=True, aliases=['randomprofle', 'randomprof', 'rprof', 'rp', 'randp'])
    async def rprofile(self, ctx):
        """Get a random profile.
        Usage: rprofile"""
        name_overrides = {
            'cvv': 'CVV',
            'cid': 'CID'
        }
        excluded = ['password', 'sexual_orientation', 'avatar', 'identifier', 'title',
                    'language', 'paypal', 'worldview', 'views_on', 'political_views',
                    'surname']
        if not ctx.message.author.avatar_url:
            ctx.message.author.avatar_url = ctx.message.author.default_avatar_url
        emb = discord.Embed(color=random.randint(1, 255**3-1))
        emb.set_author(name=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
        p = elizabeth.Personal()
        traits = {}
        calls = {d: getattr(p, d) for d in dir(p) if (not d.startswith('_')) and hasattr(getattr(p, d), '__call__')}
        for call in calls:
            if call not in excluded:
                if call in name_overrides:
                    f_name = name_overrides[call]
                else:
                    f_name = call.replace('_', ' ').title()
                traits[f_name] = calls[call]()
        emb.set_thumbnail(url=p.avatar())
        emb.title = traits['Full Name'].split()[0]
        for trait in traits:
            emb.add_field(name=trait, value=str(traits[trait]))
        await self.bot.say(embed=emb)

    @commands.cooldown(1, 5.75, type=commands.BucketType.user)
    @commands.command(pass_context=True, aliases=['qr', 'makeqr', 'qrmake'])
    async def qrcode(self, ctx, *, text: str):
        """Create a QR code.
        Usage: qrcode [text to use]"""
        img_bytes = BytesIO()
        image = await self.loop.run_in_executor(None, qrcode.make, text)
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        await self.bot.send_file(ctx.message.channel, img_bytes, filename='qrcode.png')

    @commands.command()
    async def avatar(self, *, target: discord.User):
        """Get someone's avatar.
        Usage: avatar [member]"""
        au = target.avatar_url
        await self.bot.say(au if au else target.default_avatar_url)

    @commands.command(pass_context=True)
    async def ocr(self, ctx):
        """OCR an image.
        Usage: ocr [attach an image]"""
        or_check_perms(ctx, ('bot_owner',))
        if not have_pil:
            await self.bot.say('The bot owner hasn\'t set up this feature!')
            return False
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        if ctx.message.attachments:
            with async_timeout.timeout(5):
                async with aiohttp.request('GET', ctx.message.attachments[0]['url']) as r:
                    raw_image = await r.read()
        else:
            await self.bot.say(':warning: No attachment found.')
            return
        img_bytes = BytesIO(raw_image)
        image = Image.open(img_bytes)
        text = tesserocr.image_to_text(image)
        if text:
            await self.bot.say(text)
        else:
            await self.bot.say('No results.')

    @commands.command(aliases=['cm_discrim'])
    async def discrim(self, *, discriminator: str):
        """Look up users by discriminator.
        Usage: discrim [discriminator]"""
        d = discriminator
        targets = list(set(str(m) for m in self.bot.get_all_members() if m.discriminator == d))
        if targets:
            await self.bot.say('**I found: **\n' + '\n'.join(targets))
        else:
            await self.bot.say('I found no matches. Maybe I\'m not in a server with them?')

    @commands.command(pass_context=True, aliases=['perms'])
    async def permissions(self, ctx):
        """Get your permissions here.
        Usage: permissions"""
        perms = ['**' + k[0].replace('_', ' ').title() + '**' for k in list(ctx.message.author.permissions_in(ctx.message.channel)) if k[1]]
        if '**Administrator**' in perms:
            perms.remove('**Administrator**')
            perms.append('be an **administrator**')
        if '**Send Tts Messages**' in perms:
            perms[perms.index('**Send Tts Messages**')] = '**Send TTS Messages**'
        await self.bot.say('You can ' + smartjoin(perms) + '!')

    @commands.group(pass_context=True, name='xkcd')
    async def cmd_xkcd(self, ctx):
        """Get a xkcd comic.
        Usage: xkcd {stuff}"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @commands.cooldown(1, 4, type=commands.BucketType.user)
    @cmd_xkcd.command(name='random')
    async def xkcd_random(self):
        """Get a random comic from xkcd.
        Usage: xkcd random"""
        comic = await xkcd.random_comic()
        emb = discord.Embed(color=random.randint(1, 255**3-1), title=comic.title)
        emb.set_image(url=comic.image_link)
        emb.set_footer(text=comic.alt_text)
        await self.bot.say(embed=emb)

    @commands.cooldown(1, 4, type=commands.BucketType.user)
    @cmd_xkcd.command(name='latest')
    async def xkcd_latest(self):
        """Get the latest comic from xkcd.
        Usage: xkcd latest"""
        comic = await xkcd.latest_comic()
        emb = discord.Embed(color=random.randint(1, 255**3-1), title=comic.title)
        emb.set_image(url=comic.image_link)
        emb.set_footer(text=comic.alt_text)
        await self.bot.say(embed=emb)

    @commands.cooldown(1, 4, type=commands.BucketType.user)
    @cmd_xkcd.command(name='number')
    async def xkcd_number(self, number: int):
        """Get the Nth comic from xkcd.
        Usage: xkcd number [number]"""
        try:
            comic = await xkcd.get_comic(number)
        except xkcd.InvalidComic:
            await self.bot.say(':warning: That comic doesn\'t exist.')
            return
        emb = discord.Embed(color=random.randint(1, 255**3-1), title=comic.title)
        emb.set_image(url=comic.image_link)
        emb.set_footer(text=comic.alt_text)
        await self.bot.say(embed=emb)

    @commands.command(aliases=['zws', 'u200b', '200b'])
    async def zwsp(self, number: int=1):
        """Output a number of ZWSPs.
        Usage: zwsp {number = 1}"""
        if number > 2000:
            await self.bot.say('I can\'t give you more than 2000 ZWSPs.')
        elif number > 0:
            await self.bot.say('\u200b' * number)
        else:
            await self.bot.say('I can\'t give you zero ZWSPs.')

    @commands.command()
    async def b64decode(self, *, b64: str):
        """Decode some base64 data.
        Usage: b64decode [base64]"""
        br = base64.b64decode(b64)
        try:
            m = br.decode('utf-8')
        except ValueError:
            m = '```' + str(br)[2:][:-1] + '```'
        await self.bot.say(m)

    @commands.command()
    async def b64encode(self, *, b64: str):
        """Encode some base64 data.
        Usage: b64encode [base64]"""
        br = base64.b64encode(b64.encode('utf-8'))
        try:
            m = br.decode('utf-8')
        except ValueError:
            m = '```' + str(br)[2:][:-1] + '```'
        await self.bot.say(m)

    @commands.command(pass_context=True, aliases=['ttsspam', 'tts_spam'])
    async def ttspam(self, ctx, *, text: str):
        """Spam a message with TTS. **This may get you banned from servers.**
        Usage: ttspam [message]"""
        or_check_perms(ctx, ('send_tts_messages', 'manage_messages'))
        m = await self.bot.say(textwrap.wrap((text + ' ') * 2000, width=2000)[0], tts=True)
        await asyncio.sleep(0.1)
        await self.bot.delete_message(m)

    @commands.command(pass_context=True, aliases=['ip', 'rdns', 'reverse_dns', 'reversedns'])
    async def ipinfo(self, ctx, *, ip: str):
        """Get the GeoIP and rDNS data for an IP.
        Usage: ipinfo [ip/domain]"""
        emb = discord.Embed(color=random.randint(1, 255**3-1))
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        emb.set_author(icon_url=avatar_link, name='IP Data')
        async with aiohttp.ClientSession(loop=self.loop) as sess:
            with async_timeout.timeout(5):
                async with sess.get('https://freegeoip.net/json/' + ip) as r:
                    data_res = await r.json()
        rdns = 'Failed to fetch'
        try:
            with async_timeout.timeout(6):
                rdns = (await self.loop.run_in_executor(None, socket.gethostbyaddr, data_res['ip']))[0]
        except Exception:
            pass
        emb.add_field(name='IP', value=data_res['ip'])
        emb.add_field(name='Reverse DNS', value=rdns)
        emb.add_field(name='Country', value=data_res['country_name'] + ' (%s)' % data_res['country_code'])
        region_val = data_res['region_name'] + ' (%s)' % data_res['region_code']
        emb.add_field(name='Region', value=(region_val if region_val != ' ()' else 'Not specified'))
        emb.add_field(name='City', value=(data_res['city'] if data_res['city'] else 'Not specified'))
        emb.add_field(name='ZIP Code', value=(data_res['zip_code'] if data_res['zip_code'] else 'Not specified'))
        emb.add_field(name='Timezone', value=(data_res['time_zone'] if data_res['time_zone'] else 'Not specified'))
        emb.add_field(name='Longitude', value=data_res['longitude'])
        emb.add_field(name='Latitude', value=data_res['latitude'])
        emb.add_field(name='Metro Code', value=(data_res['metro_code'] if data_res['metro_code'] != 0 else 'Not specified'))
        await self.bot.send_message(ctx.message.channel, embed=emb)

    @commands.command()
    async def dial(self, *, number: str):
        """Dial someone on the phone!
        Usage: dial [phone number]"""
        self.logger.info('Dialing ' + number + '...')
        await self.bot.say(':telephone: **Dialing {}...**'.format(number))
        await asyncio.sleep((random.randint(1, 3) + random.uniform(0, 1)) * random.uniform(0.4, 1.6) + random.uniform(0, 1))
        await self.bot.say('**No answer.**')

    @commands.command(aliases=['define'])
    async def urban(self, *, term: str):
        """Define something, according to Urban Dictionary.
        Usage: urban [term]"""
        async with aiohttp.ClientSession(loop=self.loop) as sess:
            with async_timeout.timeout(5):
                async with sess.get('http://api.urbandictionary.com/v0/define', params={'term': term}) as r:
                    data_res = await r.json()
        try:
            word = data_res['list'][0]
        except IndexError:
            await self.bot.say('No results.')
            return
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        emb = discord.Embed(color=random.randint(0, 255**3-1), title=word['word'])
        emb.set_author(name='Urban Dictionary', url=word['permalink'], icon_url='https://images.discordapp.net/.eJwFwdsNwyAMAMBdGICHhUPIMpULiCAlGIHzUVXdvXdf9cxLHeoUGeswJreVeGa9hCfVoitzvQqNtnTi25AIpfMuXZaBDSM4G9wWAdA5vxuIAQNCQB9369F7a575pv7KLUnjTvOjR6_q9wdVRCZ_.BorCGmKDHUzN6L0CodSwX7Yv3kg')
        emb.set_footer(text=datetime.now().strftime(absfmt))
        definition = word['definition']
        if definition:
            def_pages = textwrap.wrap(definition, width=1024)
            for pg in def_pages[:3]:
                emb.add_field(name='Definition', value=pg, inline=False)
        else:
            emb.add_field(name='Definition', value='None?!?!', inline=False)

        example = word['example']
        if example:
            ex_pages = textwrap.wrap(example, width=1024)
            for pg in ex_pages[:3]:
                emb.add_field(name='Example', value=pg, inline=False)
        else:
            emb.add_field(name='Example', value='None?!?!', inline=False)

        emb.add_field(name='👍', value=word['thumbs_up'])
        emb.add_field(name='👎', value=word['thumbs_down'])
        await self.bot.say(embed=emb)

    @commands.command(aliases=['nickname', 'setnick'])
    async def nick(self, *, nick: str):
        """Set your nickname.
        Usage: nick [new nickname]"""
        if ctx.message.author.server_permissions.change_nickname:
            await self.bot.change_nickname(ctx.message.author, nick)
            await self.bot.say('Done! :thumbsup:')
        else:
            await self.bot.say(':thumbsdown: You don\'t have the permission to change your nickname. Contact an admin.')

    @commands.command()
    async def bleach(self):
        """Get some bleach. NOW.
        Usage: bleach"""
        emb = discord.Embed(color=random.randint(0, 255**3-1), title='Bleach')
        emb.set_image(url='https://upload.wikimedia.org/wikipedia/commons/d/d3/Clorox_Bleach_products.jpg')
        await self.bot.say(embed=emb)

    @commands.command()
    async def mcskin(self, *, username: str):
        """Get a Minecraft player's skin.
        Usage: mcskin [username]"""
        un = username.replace('\u200b', '').replace('/', '').replace('\u200e', '')
        if not re.match(r'[a-zA-Z0-9_]+', un):
            await self.bot.say(':warning: Invalid username.')
        emb = discord.Embed(color=random.randint(0, 255**3-1), title=un + "'s skin")
        emb.set_image(url='https://mcapi.ca/skin/' + un + '/150/true')
        await self.bot.say(embed=emb)

    @commands.command()
    async def mchead(self, *, username: str):
        """Get a Minecraft player's head.
        Usage: mchead [username]"""
        un = username.replace('\u200b', '').replace('/', '').replace('\u200e', '')
        if not re.match(r'[a-zA-Z0-9_]+', un):
            await self.bot.say(':warning: Invalid username.')
        emb = discord.Embed(color=random.randint(0, 255**3-1), title=un + "'s head")
        emb.set_image(url='https://mcapi.ca/avatar/' + un + '/150/true')
        await self.bot.say(embed=emb)

def setup(bot):
    c = Utility(bot)
    bot.add_cog(c)
