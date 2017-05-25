"""Definition of the bot's Voice module."""
import asyncio
import discord
import discord.voice_client as dvclient
import io
import os
import functools
import random
import shlex
import time
import traceback
import subprocess
import textwrap
import async_timeout
import math
import threading
import util.commands as commands
from datetime import datetime
from urllib.parse import urlencode
from gtts_token import gtts_token
from util.perms import or_check_perms
from util.func import assert_msg, check
from util.const import sem_cells
import util.dynaimport as di
from .cog import Cog

youtube_dl = di.load('youtube_dl')

def clean_state(state, stop_player=True):
    loop = state.bot.loop
    if stop_player:
        state.audio_player.cancel()
    if state.current:
        player = state.current.player
        player.stop()
        player.process.kill()
        if player.process.poll() is None:
            loop.create_task(loop.run_in_executor(None, player.process.wait))
    for e in state.songs._queue:
        e.player.stop()
        e.player.process.kill()
        if e.player.process.poll() is None:
            loop.create_task(loop.run_in_executor(None, e.player.process.wait))

class StreamPlayer(dvclient.StreamPlayer):
    def __init__(self, stream, encoder, connected, player, after, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.daemon = True
        self.buff = stream
        self.frame_size = encoder.frame_size
        self.player = player
        self._end = threading.Event()
        self._resumed = threading.Event()
        self._resumed.set() # we are not paused
        self._connected = connected
        self.after = after
        self.delay = encoder.frame_length / 1000.0
        self._current_error = None

    def _do_run(self):
        self.loops = 0
        self._start = time.time()
        while not self._end.is_set():
            # are we paused?
            if not self._resumed.is_set():
                # wait until we aren't
                self._resumed.wait()

            if not self._connected.is_set():
                self.stop()
                break

            self.loops += 1
            data = self.buff.read(self.frame_size)

            if len(data) != self.frame_size:
                self.stop()
                break

            self.player(data)
            next_time = self._start + self.delay * self.loops
            delay = max(0, self.delay + (next_time - time.time()))
            time.sleep(delay)

class ProcessPlayer(StreamPlayer): 
    def __init__(self, process, client, after, **kwargs):
        super().__init__(process.stdout, client.encoder,
                         client._connected, client.play_audio, after, **kwargs)
        self.process = process # here we don't need automatic cleanup

class VoiceEntry:
    """Class to represent an entry in the standard voice queue."""
    def __init__(self, message, player, override_name=None):
        self.requester = message.author
        self.channel = message.channel
        self.player = player
        self.name = override_name

    def __str__(self) -> str:
        fmt = '**{}**'
        p = self.player
        tags = []
        fmt = fmt.format(self.get_name())
        try:
            if p.uploader:
                tags.append('uploader *{}*'.format(p.uploader))
        except AttributeError:
            pass
        if self.requester:
            tags.append('requester *{}*'.format(self.requester.display_name))
        try:
            if p.duration:
                tags.append('duration *{0[0]}m, {0[1]}s*'.format(list(map(int, divmod(p.duration, 60)))))
        except AttributeError:
            pass
        if tags:
            fmt += ' - ' + ', '.join(tags)
        return fmt

    def get_name(self) -> str:
        """Get the name (title) of this player."""
        def _seg2():
            if self.name:
                return self.name
            else:
                try:
                    return self.player.title
                except AttributeError:
                    return 'No title specified'
        try:
            if self.player.title == 'translate_tts':
                return 'Speech'
            else:
                return _seg2()
        except AttributeError:
            return _seg2()
    def get_desc(self) -> str:
        fmt = ''
        p = self.player
        tags = []
        try:
            if p.uploader:
                tags.append('Uploader: *{0}*'.format(p.uploader))
        except AttributeError:
            pass
        if self.requester:
            tags.append('Requester: *{0}*'.format(self.requester.display_name))
        try:
            if p.duration:
                tags.append('Duration: *{0[0]}m, {0[1]}s*'.format(list(map(int, divmod(p.duration, 60)))))
        except AttributeError:
            pass
        if tags:
            fmt += '\n'.join(tags)
        if not fmt:
            fmt = 'No details specified!'
        return fmt

class VoiceState:
    """Class for handling any voice-related actions."""
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())
        self.create_time = datetime.now()
        self.cog = bot.cogs['Voice']
        self.have_played = False

    def is_playing(self):
        """Check if anything is currently playing."""
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        """Get the current player object."""
        return self.current.player

    def skip(self):
        """Skip the currently playing song."""
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        """Play the next song in queue."""
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        """Handle the queue and playing of voice entries."""
        while True:
            self.play_next_song.clear()
            if self.songs._queue or not self.have_played:
                self.current = await self.songs.get()
            else:
                try:
                    clean_state(self, stop_player=False)
                except Exception as e:
                    self.logger.exception(e)
                    if self.bot.id == '239775420470394897':
                        await self.bot.send_message(discord.Object(id='244641688981733386'), '**Voice clean_state error!**\n```py\n' + ''.join(traceback.format_tb(e.__traceback__)) + '\n' + e.__class__.__name__ + ': ' + str(e) + '```')
                await self.voice.disconnect()
                del self.cog.voice_states[self.voice.channel.server.id]
                return
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()
            self.have_played = True

class Voice(Cog):
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.voice_states = {}
        self.tokenizer = gtts_token.Token()
        self.servers_recording = set()
        super().__init__(bot)
        self.logger = self.logger.getChild('voice')
        self.disconnect_task = self.loop.create_task(self.disconnect_bg_task())

    def get_voice_state(self, server):
        """Get the current VoiceState object."""
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def disconnect_bg_task(self):
        """Background task to disconnect from voice channels if idle."""
        while True:
            for sid, state in list(self.voice_states.items())[:]:
                if (datetime.now() - state.create_time).total_seconds() < 300:
                    continue # 5 mins
                if state.voice:
                    if state.voice.channel is None:
                        continue
                    mm = [m for m in state.voice.channel.voice_members if not \
                            (m.voice.deaf or m.voice.self_deaf) and m.id != self.bot.user.id]
                    if len(mm) < 1:
                        try:
                            clean_state(state)
                        except Exception as e:
                            self.logger.exception(e)
                            if self.bot.id == '239775420470394897':
                                await self.bot.send_message(discord.Object(id='244641688981733386'), '**Voice clean_state error!**\n```py\n' + ''.join(traceback.format_tb(e.__traceback__)) + '\n' + e.__class__.__name__ + ': ' + str(e) + '```')
                        await state.voice.disconnect()
                        del self.voice_states[sid]
                        self.logger.info('Pruned a voice state! Server ID: ' + sid + \
                              ', server name: ' + state.voice.channel.server.name)
                else:
                    try:
                        clean_state(state)
                    except Exception as e:
                        self.logger.exception(e)
                        if self.bot.id == '239775420470394897':
                            await self.bot.send_message(discord.Object(id='244641688981733386'), '**Voice clean_state error!**\n```py\n' + ''.join(traceback.format_tb(e.__traceback__)) + '\n' + e.__class__.__name__ + ': ' + str(e) + '```')
                    del self.voice_states[sid]
                    self.logger.info('Pruned a ghost voice state! Server ID: ' + sid)
            await asyncio.sleep(300) # every 5 min

    async def create_voice_client(self, channel):
        """Create a new voice client on a specified channel."""
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass
        self.disconnect_task.cancel()

    @commands.command(no_pm=True)
    async def join(self, *, channel: discord.Channel):
        """Joins a voice channel.
        Usage: join [channel]"""
        try:
            await self.create_voice_client(channel)
        except discord.InvalidArgument:
            await self.bot.say('That\'s not a voice channel!')
        except discord.ClientException:
            await self.bot.say('Already in a voice channel.')
        else:
            await self.bot.say('Ready to play audio in **' + channel.name + '**!')

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel.
        Usage: summon"""
        summoned_channel = ctx.message.author.voice_channel
        if not summoned_channel:
            await self.bot.say('You aren\'t in a voice channel.')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
            try:
                await state.voice.enable_voice_events()
            except AttributeError:
                pass
        else:
            await state.voice.move_to(summoned_channel)
        if ctx.invoked_with == 'summon':
            await self.bot.say('Ready to play audio in **' + summoned_channel.name + '**!')

        return True

    @commands.command(pass_context=True, no_pm=True, aliases=['yt', 'youtube'])
    async def play(self, ctx, *, song: str):
        """Plays a song.
        Adds the requested song to the playlist (queue) for playing.
        This command automatically searches from sites like YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        Usage: play [song/video name]"""
        state = self.get_voice_state(ctx.message.server)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return
        if state.voice.channel != ctx.message.author.voice_channel:
            await self.bot.say('You can only modify the queue if you\'re in the same channel as me!')
            return
        if len(state.songs._queue) >= 5:
            await self.bot.say('There can only be up to 5 items in queue!')
            return

        state.voice.encoder_options(sample_rate=48000, channels=2)
        try:
            player = await self.create_ytdl_player(state.voice, song, after=state.toggle_next)
        except Exception as e:
            n = type(e).__name__
            if n.endswith('DownloadError') or n.endswith('IndexError'):
                await self.bot.say('**That video couldn\'t be found!**')
                return False
            else:
                raise e
        try:
            if player.duration > 8600:
                await self.bot.say(':warning: Song can\'t be longer than 2h22m.')
                return
        except TypeError: # livestream, no duration
            pass

        entry = VoiceEntry(ctx.message, player)
        before = bool(state.current)
        await state.songs.put(entry)
        if before:
            await self.bot.say('Queued ' + str(entry))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pause the current song.
        Usage: pause"""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()
            await self.bot.say('Paused.')

    @commands.command(pass_context=True, no_pm=True, aliases=['unpause'])
    async def resume(self, ctx):
        """Resume the current song.
        Usage: resume"""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()
            await self.bot.say('Resumed.')

    @commands.command(pass_context=True, no_pm=True, aliases=['disconnect'])
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        Usage: stop
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            clean_state(state)
            await state.voice.disconnect()
            del self.voice_states[server.id]
            await self.bot.say('Stopped.')
        except:
            await self.bot.say('Couldn\'t stop. Use `force_disconnect` if this doesn\'t work.')
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def force_disconnect(self, ctx):
        """Force disconnect from the current server's voice channel.
        Useful when the stop command doesn't work.
        Usage: force_disconnect"""
        match_clients = [c for c in self.bot.voice_clients if c.channel is not None \
                         and c.channel.server.id == ctx.message.server.id]
        if match_clients:
            success = []
            for matched in match_clients:
                if matched.is_connected():
                    await matched.disconnect()
                    if matched.channel.server.id in self.voice_states:
                        del self.voice_states[matched.channel.server.id]
                    success.append(True)
            if True in success:
                await self.bot.say('Disconnected!')
            else:
                await self.bot.say('I found a voice client, but it\'s not connected.')
        else:
            await self.bot.say('I\'m not connected to any channels here.')

    @commands.command(pass_context=True, no_pm=True, aliases=['next'])
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        Usage: skip
        """
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            await self.bot.say('Not playing any music right now...')
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            await self.bot.say('Requester of song requested to skip, skipping...')
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            need_votes = math.ceil(len(state.voice.channel.voice_members) / 2)
            if total_votes >= need_votes:
                await self.bot.say('Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.bot.say('Skip vote added, currently at [{}/{}]'.format(total_votes, need_votes))
        else:
            await self.bot.say('You\'ve already voted to skip this song.')

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song.
        Usage: playing"""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
        else:
            skip_count = len(state.skip_votes)
            await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))

    @commands.command(pass_context=True, no_pm=True, aliases=['gspeak'])
    async def speak(self, ctx, *, text: str):
        """Uses a TTS voice to speak a message.
        Usage: speak [message]"""
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'user-agent': 'stagefright/1.2 (Linux;Android 5.0)',
            'referer': 'https://translate.google.com/'
        }
        base_url = 'http://translate.google.com/translate_tts'
        if len(text) > 400:
            await self.bot.say('Hmm, that text is too long. I\'ll cut it to 400 characters.')
            text = text[:400]
        rounds = textwrap.wrap(text, width=100)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return
        if state.voice.channel != ctx.message.author.voice_channel:
            await self.bot.say('You can only modify the queue if you\'re in the same channel as me!')
            return
        if len(state.songs._queue) >= 5:
            await self.bot.say('There can only be up to 5 items in queue!')
            return

        for intxt in rounds:
            g_args = {
                'ie': 'UTF-8',
                'q': intxt,
                'tl': 'en-us',
                'client': 'tw-ob',
                'idx': '0',
                'total': '1',
                'textlen': '12',
                'tk': str(self.tokenizer.calculate_token(intxt))
            }
            player = await self.create_ytdl_player(state.voice, base_url + '?' + urlencode(g_args), ytdl_options=opts, after=state.toggle_next)
            entry = VoiceEntry(ctx.message, player)
            before = bool(state.current)
            await state.songs.put(entry)
            if before:
                await self.bot.say('Queued **Speech**! :smiley:')
            await asyncio.sleep(1)

    @commands.command(pass_context=True, aliases=['quene'])
    async def queue(self, ctx):
        """Get the current song queue.
        Usage: queue"""
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            await self.bot.say('**Not in a voice channel!**')
            return False
        if not state.songs:
            await self.bot.say('**Song queue is empty!**')
            return False
        if (not state.songs._queue) and (not state.current):
            await self.bot.say('**Song queue is empty!**')
            return False
        target = self.bot.user
        au = target.avatar_url
        avatar_link = (au if au else target.default_avatar_url)
        if (not state.songs._queue) and (state.current):
            key_str = 'are no songs in queue. One is playing right now.'
        elif state.songs._queue:
            key_str = 'is 1 song playing, and %s in queue.' % str(len(state.songs._queue))
        emb = discord.Embed(color=random.randint(0, 256**3-1), title='Voice Queue', description='There ' + key_str)
        emb.set_author(name=target.display_name, url='https://blog.khronodragon.com/', icon_url=avatar_link)
        emb.set_footer(text='Best bot! :3', icon_url=avatar_link)
        if state.current:
            emb.add_field(name='**[NOW PLAYING]** ' + state.current.get_name(), value=state.current.get_desc(), inline=False)
        else:
            await self.bot.say('**Not playing anything right now!**')
            return False
        for e in state.songs._queue:
            emb.add_field(name=e.get_name(), value=e.get_desc())
        await self.bot.say('🎶🎵', embed=emb)

    async def on_ready(self):
        if self.bot.selfbot:
            self.logger.info('This is a selfbot, unloading voice. Discord\'s TOS doesn\'t allow selfbots to stream music.')
            self.bot.unload_extension('default_cogs.voice')

    async def create_ytdl_player(self, vclient, url, *, ytdl_options=None, **kwargs):
        """|coro|
        Creates a stream player for youtube or other services that launches
        in a separate thread to play the audio.
        The player uses the ``youtube_dl`` python library to get the information
        required to get audio from the URL. Since this uses an external library,
        you must install it yourself. You can do so by calling
        ``pip install youtube_dl``.
        You must have the ffmpeg or avconv executable in your path environment
        variable in order for this to work.
        The operations that can be done on the player are the same as those in
        :meth:`create_stream_player`. The player has been augmented and enhanced
        to have some info extracted from the URL. If youtube-dl fails to extract
        the information then the attribute is ``None``. The ``yt``, ``url``, and
        ``download_url`` attributes are always available.
        +---------------------+---------------------------------------------------------+
        |      Operation      |                       Description                       |
        +=====================+=========================================================+
        | player.yt           | The `YoutubeDL <ytdl>` instance.                        |
        +---------------------+---------------------------------------------------------+
        | player.url          | The URL that is currently playing.                      |
        +---------------------+---------------------------------------------------------+
        | player.download_url | The URL that is currently being downloaded to ffmpeg.   |
        +---------------------+---------------------------------------------------------+
        | player.title        | The title of the audio stream.                          |
        +---------------------+---------------------------------------------------------+
        | player.description  | The description of the audio stream.                    |
        +---------------------+---------------------------------------------------------+
        | player.uploader     | The uploader of the audio stream.                       |
        +---------------------+---------------------------------------------------------+
        | player.upload_date  | A datetime.date object of when the stream was uploaded. |
        +---------------------+---------------------------------------------------------+
        | player.duration     | The duration of the audio in seconds.                   |
        +---------------------+---------------------------------------------------------+
        | player.likes        | How many likes the audio stream has.                    |
        +---------------------+---------------------------------------------------------+
        | player.dislikes     | How many dislikes the audio stream has.                 |
        +---------------------+---------------------------------------------------------+
        | player.is_live      | Checks if the audio stream is currently livestreaming.  |
        +---------------------+---------------------------------------------------------+
        | player.views        | How many views the audio stream has.                    |
        +---------------------+---------------------------------------------------------+
        Parameters
        -----------
        url : str
            The URL that ``youtube_dl`` will take and download audio to pass
            to ``ffmpeg`` or ``avconv`` to convert to PCM bytes.
        ytdl_options : dict
            A dictionary of options to pass into the ``YoutubeDL`` instance.
            See `the documentation <ytdl>`_ for more details.
        \*\*kwargs
            The rest of the keyword arguments are forwarded to
            :func:`create_ffmpeg_player`.
        Raises
        -------
        ClientException
            Popen failure from either ``ffmpeg``/``avconv``.
        Returns
        --------
        StreamPlayer
            An augmented StreamPlayer that uses ffmpeg.
            See :meth:`create_stream_player` for base operations.
        """
        opts = {
            'format': 'webm[abr>0]/bestaudio',
            'default_search': 'ytsearch',
            'quiet': True,
            'source_address': '0.0.0.0',
            'extractaudio': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'outtmpl': 'data/voice/cache/%(id)s'
        }

        if ytdl_options is not None and isinstance(ytdl_options, dict):
            opts.update(ytdl_options)

        ydl = youtube_dl.YoutubeDL(opts)
        func = functools.partial(ydl.extract_info, url, download=False)
        info = await self.loop.run_in_executor(None, func)
        if "entries" in info:
            info = info['entries'][0]

        self.logger.info('Playing "{}" with youtube_dl'.format(url))
        download_url = info['url']
        player = self.create_yt_ffmpeg_player(vclient, download_url, **kwargs)

        # set the dynamic attributes from the info extraction
        player.download_url = download_url
        player.url = url
        player.yt = ydl
        player.views = info.get('view_count')
        player.is_live = bool(info.get('is_live'))
        player.likes = info.get('like_count')
        player.dislikes = info.get('dislike_count')
        player.duration = info.get('duration')
        player.uploader = info.get('uploader')

        is_twitch = 'twitch' in url
        if is_twitch:
            # twitch has 'title' and 'description' sort of mixed up.
            player.title = info.get('description')
            player.description = None
        else:
            player.title = info.get('title')
            player.description = info.get('description')

        # upload date handling
        date = info.get('upload_date')
        if date:
            try:
                date = datetime.strptime(date, '%Y%M%d').date()
            except ValueError:
                date = None

        player.upload_date = date
        return player

    def create_yt_ffmpeg_player(self, vclient, filename, *, use_avconv=False, pipe=False, stderr=None, options=None, before_options=None, headers=None, after=None):
        """Creates a stream player for ffmpeg that launches in a separate thread to play
        audio.
        The ffmpeg player launches a subprocess of ``ffmpeg`` to a specific
        filename and then plays that file.
        You must have the ffmpeg or avconv executable in your path environment variable
        in order for this to work.
        The operations that can be done on the player are the same as those in
        :meth:`create_stream_player`.
        Parameters
        -----------
        filename
            The filename that ffmpeg will take and convert to PCM bytes.
            If ``pipe`` is True then this is a file-like object that is
            passed to the stdin of ``ffmpeg``.
        use_avconv: bool
            Use ``avconv`` instead of ``ffmpeg``.
        pipe : bool
            If true, denotes that ``filename`` parameter will be passed
            to the stdin of ffmpeg.
        stderr
            A file-like object or ``subprocess.PIPE`` to pass to the Popen
            constructor.
        options : str
            Extra command line flags to pass to ``ffmpeg`` after the ``-i`` flag.
        before_options : str
            Command line flags to pass to ``ffmpeg`` before the ``-i`` flag.
        headers: dict
            HTTP headers dictionary to pass to ``-headers`` command line option
        after : callable
            The finalizer that is called after the stream is done being
            played. All exceptions the finalizer throws are silently discarded.
        Raises
        -------
        ClientException
            Popen failed to due to an error in ``ffmpeg`` or ``avconv``.
        Returns
        --------
        StreamPlayer
            A stream player with specific operations.
            See :meth:`create_stream_player`.
        """
        command = 'ffmpeg' if not use_avconv else 'avconv'
        input_name = '-' if pipe else shlex.quote(filename)
        before_args = ""
        if isinstance(headers, dict):
            for key, value in headers.items():
                before_args += "{}: {}\r\n".format(key, value)
            before_args = ' -headers ' + shlex.quote(before_args)

        if isinstance(before_options, str):
            before_args += ' ' + before_options

        cmd = command + '{} -i {} -f s16le -ar {} -ac {} -loglevel warning'
        cmd = cmd.format(before_args, input_name, vclient.encoder.sampling_rate, vclient.encoder.channels)

        if isinstance(options, str):
            cmd = cmd + ' ' + options

        cmd += ' pipe:1'

        stdin = None if not pipe else filename
        args = shlex.split(cmd)
        try:
            p = subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)
            return ProcessPlayer(p, vclient, after)
        except FileNotFoundError as e:
            raise discord.ClientException('ffmpeg/avconv was not found in your PATH environment variable') from e
        except subprocess.SubprocessError as e:
            raise discord.ClientException('Popen failed: {0.__name__} {1}'.format(type(e), str(e))) from e

def setup(bot):
    paths = (
        ('data', 'voice'),
        ('data', 'voice', 'cache'),
    )
    for p in paths:
        rpath = os.path.join(bot.dir, *p)
        if not os.path.exists(rpath):
            os.makedirs(rpath)
    c = Voice(bot)
    bot.add_cog(c)
