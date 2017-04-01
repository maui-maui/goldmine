"""Definition of the bot's Voice module."""
from datetime import datetime
from urllib.parse import urlencode
from gtts_token import gtts_token
from util.perms import or_check_perms
from util.func import assert_msg, check
from util.const import sem_cells
import util.dynaimport as di
from .cog import Cog

for mod in ['asyncio', 'random', 'io', 'subprocess', 'textwrap', 'async_timeout',
            'discord', 'math', 'os']:
    globals()[mod] = di.load(mod)
commands = di.load('util.commands')

options = {
    'default_search': 'ytsearch',
    'quiet': True,
    'source_address': '0.0.0.0',
    'format': 'bestaudio/best',
    'extractaudio': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'no_warnings': True,
    'outtmpl': 'data/voice/cache/%(id)s'
}
# >​
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
        if self.current:
            self.current.player.stop()
            self.current.player.process.kill()
            if self.current.player.process.poll() is None:
                self.bot.loop.create_task(self.bot.loop.run_in_executor(None,
                                          self.current.player.process.communicate))
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        """Handle the queue and playing of voice entries."""
        while True:
            self.play_next_song.clear()
            if self.songs._queue:
                self.current = await self.songs.get()
            else:
                if self.current:
                    self.current.player.stop()
                    self.current.player.process.kill()
                    if self.current.player.process.poll() is None:
                        self.bot.loop.create_task(self.bot.loop.run_in_executor(None, self.current.player.process.communicate))
                for p in self.songs._queue:
                    p.stop()
                    p.process.kill()
                    if p.process.poll() is None:
                        self.bot.loop.create_task(self.bot.loop.run_in_executor(None, p.process.communicate))
                await self.voice.disconnect()
                del self.cog.voice_states[self.voice.channel.server.id]
                return
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Voice(Cog):
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.voice_states = {}
        self.tokenizer = gtts_token.Token()
        self.servers_recording = set()
        self.recording_data = {}
        self.opus_decoder = None
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
                thing = False
                if (datetime.now() - state.create_time).total_seconds() < 300:
                    continue # 5 mins
                if state.voice:
                    if len([m for m in state.voice.channel.voice_members if not \
                            (m.voice.deaf or m.voice.self_deaf) and m.id != self.bot.user.id]) < 1:
                        state.audio_player.cancel()
                        if state.current:
                            state.current.player.stop()
                            state.current.player.process.kill()
                            if state.current.player.process.poll() is None:
                                self.loop.create_task(self.loop.run_in_executor(None, state.current.player.process.communicate))
                        for p in state.songs._queue:
                            p.stop()
                            p.process.kill()
                            if p.process.poll() is None:
                                self.loop.create_task(self.loop.run_in_executor(None, p.process.communicate))
                        await state.voice.disconnect()
                        del self.voice_states[sid]
                        self.logger.info('Pruned a voice state! Server ID: ' + sid + \
                              ', server name: ' + state.voice.channel.server.name)
                else:
                    state.audio_player.cancel()
                    del self.voice_states[sid]
                    self.logger.info('Pruned a ghost voice state! Server ID: ' + sid)
            await asyncio.sleep(300) # every 5 min

    async def create_voice_client(self, channel):
        """Create a new voice client on a specified channel."""
        voice = await self.bot.join_voice_channel(channel)
        try:
            await voice.enable_voice_events()
        except AttributeError:
            pass
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

    async def on_speaking(self, speaking, uid):
        """Event for when someone is speaking."""
        pass

    async def on_speak(self, data, timestamp, voice):
        """Event for when a voice packet is received."""
        if voice.server.id in self.servers_recording:
            decoded_data = await self.loop.run_in_executor(None, self.opus_decoder.decode, data, voice.encoder.frame_size)
            try:
                self.recording_data[voice.server.id] += decoded_data
            except KeyError:
                self.recording_data[voice.server.id] = decoded_data

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
        await self.bot.say('Ready to play audio in **' + summoned_channel.name + '**!')

        return True

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

        status = await self.bot.say('Loading... 🌚')
        pg_task = self.loop.create_task(asyncio.wait_for(self.progress(status, 'Loading'), timeout=30, loop=self.loop))
        state.voice.encoder_options(sample_rate=48000, channels=2)
        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=options, after=state.toggle_next)
        except Exception as e:
            n = type(e).__name__
            if n.endswith('DownloadError') or n.endswith('IndexError'):
                pg_task.cancel()
                self.loop.create_task(self.bot.delete_message(status))
                await self.bot.say('**That video couldn\'t be found!**')
                return False
            else:
                raise e
        try:
            if player.duration > 8600:
                await self.bot.say(':warning: Song can\'t be longer than 2h22m.')
                return
        except TypeError: # livestream, no duration
            return

        player.volume = 0.7
        entry = VoiceEntry(ctx.message, player)
        was_empty = state.songs.empty()
        await state.songs.put(entry)
        if state.current:
            await self.bot.say('Queued ' + str(entry))
        pg_task.cancel()
        await self.bot.delete_message(status)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value: int):
        """Sets the volume of the currently playing song.
        Usage: volume [percentage, 1-100]"""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            if (value >= 10) and (value <= 200):
                player.volume = value / 100
                await self.bot.say('**Volume is now {:.0%}.**'.format(player.volume))
            else:
                await self.bot.say('**Volume must be in the range of 10% and 200%!**')

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song.
        Usage: pause"""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()
            await self.bot.say('Paused.')

    @commands.command(pass_context=True, no_pm=True, aliases=['unpause'])
    async def resume(self, ctx):
        """Resumes the current song OR resume suspended bot features.
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
            state.audio_player.cancel()
            if state.current:
                state.current.player.stop()
                state.current.player.process.kill()
                if state.current.player.process.poll() is None:
                    self.loop.create_task(self.loop.run_in_executor(None, state.current.player.process.communicate))
            for p in state.songs._queue:
                p.stop()
                p.process.kill()
                if p.process.poll() is None:
                    self.loop.create_task(self.loop.run_in_executor(None, p.process.communicate))
            del self.voice_states[server.id]
            await state.voice.disconnect()
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
            if match_clients[0].is_connected():
                await match_clients[0].disconnect()
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

    @commands.command(pass_context=True, no_pm=True)
    async def picospeak(self, ctx, *, tospeak: str):
        """Uses the SVOX pico TTS engine to speak a message.
        Usage: picospeak [message]"""
        or_check_perms(ctx, ('bot_owner',))
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

        stream = io.BytesIO(subprocess.check_output(['pico2wave', '-w', '/tmp/pipe.wav', tospeak]))
        state.voice.encoder_options(sample_rate=16000, channels=1)
        player = state.voice.create_stream_player(stream, after=state.toggle_next)
        player.volume = 1.0
        entry = VoiceEntry(ctx.message, player, override_name='Speech')
        await state.songs.put(entry)
        await self.bot.say('Queued ' + str(entry))
        state.voice.encoder_options(sample_rate=48000, channels=2)

    @commands.command(pass_context=True, no_pm=True, aliases=['gspeak'])
    async def speak(self, ctx, *, text: str):
        """Uses a TTS voice to speak a message.
        Usage: speak [message]"""
        state = self.get_voice_state(ctx.message.server)
        opts = {
            **options,
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
            await self.bot.say('Adding to voice queue:```' + intxt + '```**It may take up to *10 seconds* to queue.**')
            player = await state.voice.create_ytdl_player(base_url + '?' + urlencode(g_args), ytdl_options=opts, after=state.toggle_next)
            player.volume = 0.75
            entry = VoiceEntry(ctx.message, player)
            await state.songs.put(entry)
            await self.bot.say('Queued **Speech**! :smiley:')
            await asyncio.sleep(1)

    @commands.group(pass_context=True, aliases=['record', 'rec'])
    async def recording(self, ctx):
        """Manage voice recording, recognition, and playback.
        Usage: recording"""
        or_check_perms(ctx, ('bot_owner',))
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @recording.command(pass_context=True, name='toggle', aliases=['start', 'stop'])
    async def record_toggle(self, ctx):
        """Toggle (start/stop) voice recording.
        Usage: recording toggle"""
        or_check_perms(ctx, ['manage_server', 'manage_channels', 'move_members'])
        if 'dispatch' in inspect.signature(VoiceClient.__init__).parameters:
            if not self.opus_decoder:
                try:
                    from opuslib import Decoder
                    self.opus_decoder = Decoder(48000, 2)
                except Exception:
                    await self.bot.say('Feature not available!')
                    return
        else:
            await self.bot.say('Feature not available!')
            return
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        sid = ctx.message.server.id
        if sid not in self.servers_recording:
            self.servers_recording.add(sid)
            await self.bot.say('**Voice in this server is now being recorded!**')
        else:
            self.servers_recording.remove(sid)
            await self.bot.say('**Voice is no longer being recorded in this server!**')

    @recording.command(pass_context=True, name='play', aliases=['echo', 'playback', 'dump'])
    async def record_play(self, ctx):
        """Play the current the voice recording.
        Usage: recording play"""
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
        with assert_msg(ctx, '**This server does not have a recording!**'):
            check(ctx.message.server.id in self.recording_data)
        state.voice.encoder_options(sample_rate=48000, channels=2)
        player = state.voice.create_stream_player(io.BytesIO(self.recording_data[ctx.message.server.id]), after=state.toggle_next)
        player.volume = 0.7
        entry = VoiceEntry(ctx.message, player, override_name='Voice Recording from ' + ctx.message.server.name)
        await state.songs.put(entry)
        await self.bot.say('Queued ' + str(entry))

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
            self.logger.info('We\'re a selfbot, unloading voice. Discord\'s TOS doesn\'t allow selfbots to stream music.')
            self.bot.unload_extension('default_cogs.voice')

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
