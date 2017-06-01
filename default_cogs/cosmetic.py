"""Definition of the bot's Cosmetic module.'"""
import asyncio
import random
import io
import aiohttp
import discord
import async_timeout
from discord.ext import commands
import util.json as json
from contextlib import suppress
from urllib.parse import urlencode
from .cog import Cog
from util.const import charsets, spinners, lvl_base
import util.dynaimport as di

imghdr = di.load('imghdr')

class Cosmetic(Cog):
    """Commands for some neat-o fun!
    Includes color changing and more.
    """

    def __init__(self, bot):
        self.playing_anim = set()
        self.stop_anim = set()
        self.al_aliases = charsets.keys()
        super().__init__(bot)

    @commands.command()
    @commands.check(commands.guild_only())
    async def emotes(self, ctx):
        """Lists all the custom emoji im this guild.
        Usage: emotes"""
        cemotes = ctx.guild.emojis
        em_string = (' '.join([str(i) for i in cemotes]) if len(cemotes) >= 1 else 'This guild has no custom emojis!')
        await ctx.send(em_string)

    @commands.command(aliases=['rev', 'mirror'])
    async def reverse(self, ctx, *, rmsg: str):
        """Reverse some text you give.
        Usage: reverse [text here]"""
        await ctx.send(':repeat: ' + rmsg[::-1])

    @commands.command(aliases=['math_sans_italic', 'circled', 'math_double', 'math_bold_italic', 'math_sans_bold_italic', 'parenthesized', 'math_bold_fraktur', 'math_sans_bold', 'squared', 'math_mono', 'fullwidth', 'squared_negative', 'normal', 'circled_negative', 'regional', 'math_sans', 'math_bold_script', 'math_bold', 'upside_down'])
    async def style(self, ctx, *rmsg):
        """Stylize text in cool alphabets! Invoke with alphabet name.
        Usage: style [style name] [text here]"""
        if rmsg:
            imsg = ' '.join(rmsg)
            final_result = self.stylize(ctx.invoked_with.lower(), imsg)
            await ctx.send(final_result)
        else:
            await ctx.send('**You must invoke this command as: `[p][name of set] [message here]`.** For example: `!math_bold hello world`! Here are the character sets available:')
            await self.fontlist.invoke(ctx)

    def stylize(self, alphabet, intxt):
        return intxt.translate(str.maketrans(charsets['normal'], charsets[alphabet]))

    @commands.command(aliases=['fonts', 'alphabet', 'alphabets', 'alphalist', 'styles', 'stylelist', 'chars', 'charlist', 'charsets', 'charsetlist'])
    async def fontlist(self, ctx):
        """List the available fancy character sets / alphabets / fonts.
        Usage: fonts"""
        pager = commands.Paginator(prefix='', suffix='')
        pager.add_line('**Listing all character sets defined with samples.**')
        for i in self.al_aliases:
            tmp = self.stylize(i, 'abcdefghijklmnopqrstuvwxyz')
            pager.add_line('**{0}**: `{1}`'.format(i, tmp))
        pager.add_line('**Invoke with `[p][name of set] [message here]`.** For example: `!math_bold hello world`.')
        for page in pager.pages:
            await ctx.send(page)

    @commands.cooldown(1, 6, type=commands.BucketType.guild)
    @commands.command(aliases=['af', 'sca', 'anim', 'a', 'playanim', 'aplay', 'animplay'])
    async def animation(self, ctx, anim_seq, runs: int):
        """Do a 0.9 fps animation x times from the given sequence.
        Usage: animation [packed animation] [number of runs]"""
        try:
            cmid = ctx.guild.id
        except AttributeError:
            cmid = ctx.author.id
        if cmid not in self.playing_anim:
            self.playing_anim.add(cmid)
            msg = await ctx.send('Starting animation...')
            for _xi in range(runs):
                for frame in anim_seq:
                    if cmid not in self.stop_anim:
                        await msg.edit(content=frame)
                        await asyncio.sleep(0.93)
                    else:
                        await msg.edit(content='**Animation stopped!**')
                        await ctx.send('**Animation stopped!**')
                        self.playing_anim.remove(cmid)
                        return
            await msg.edit(content='**Animation stopped!**')
            await ctx.send('**Animation stopped!**')
            self.playing_anim.remove(cmid)
        else:
            await ctx.send('**Already playing an animation in this guild!**')

    @commands.command(aliases=['sa', 'ssca', 'sanim', 'stopanimation', 'animstop', 'saf'])
    async def stopanim(self, ctx):
        """Stop the animation playing in this guild, if any.
        Usage: stopanim"""
        try:
            cmid = ctx.guild.id
        except AttributeError:
            cmid = ctx.author.id
        if cmid in self.playing_anim:
            await ctx.send('**Stopping animation...**')
            self.stop_anim.add(cmid)
            await asyncio.sleep(1.9)
            try:
                self.stop_anim.remove(cmid)
            except KeyError:
                pass
        else:
            await ctx.send('**Not playing any animation here!**')

    @commands.command(aliases=['lanim', 'listanims', 'listanim', 'animationlist', 'animl', 'anims', 'animations', 'al', 'packs', 'packed', 'pal', 'pa', 'alist'])
    async def animlist(self, ctx):
        """List the packed animations I have saved.
        Usage: animlist"""
        await ctx.send('**Listing stored packed animations.**\n```\n' + '\n'.join(spinners) + '```')

    @commands.command(aliases=['random.cat', 'randomcat', 'rcat', 'cats', 'catrandom', 'random_cat'])
    async def cat(self, ctx):
        """Get a random cat! Because why not.
        Usage: cat"""
        with async_timeout.timeout(8):
            async with self.bot.cog_http.get('http://random.cat/meow') as response:
                ret = await response.json()
        e = discord.Embed(color=random.randint(1, 255**3-1))
        e.set_image(url=ret['file'])
        await ctx.send(embed=e)

    @commands.command(aliases=['temote', 'bemote', 'dcemote', 'getemote', 'fetchemote'])
    async def emote(self, ctx, emote: str):
        """Get a Twitch, FrankerFaceZ, BetterTTV, or Discord emote.
        Usage: emote [name of emote]"""
        emote = emote.replace(':', '')
        with async_timeout.timeout(13):
            try:
                async with self.bot.cog_http.get('https://static-cdn.jtvnw.net/emoticons/v1/' + str(self.bot.emotes['twitch'][emote]['image_id']) + '/1.0') as resp:
                    emote_img = await resp.read()
            except KeyError: # let's try frankerfacez
                try:
                    async with self.bot.cog_http.get('https://cdn.frankerfacez.com/emoticon/' + str(self.bot.emotes['ffz'][emote]) + '/1') as resp:
                        emote_img = await resp.read()
                except KeyError: # let's try BetterTTV
                    try:
                        async with self.bot.cog_http.get(self.bot.emotes['bttv'][emote]) as resp:
                            emote_img = await resp.read()
                    except KeyError: # let's try Discord
                        await ctx.send('**No such emote!** I can fetch from Twitch, FrankerFaceZ, BetterTTV, or Discord (soon).')
                        return False
        img_bytes = io.BytesIO(emote_img)
        ext = imghdr.what(img_bytes)
        await ctx.send(file=discord.File(img_bytes, f'emote.{ext}'))

def setup(bot):
    c = Cosmetic(bot)
    bot.add_cog(c)
